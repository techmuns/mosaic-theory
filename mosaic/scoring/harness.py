"""Scoring harness — score the decision ledger against stored forward EOD prices.

For each verdict it computes the name's return from the **frozen entry price** to the scoring date
(the thesis horizon once it has passed, else an interim mark) and the benchmark's return over the
same window, then aggregates the resolved verdicts into the report (see ``mosaic.scoring.metrics``).
Verdicts whose horizon hasn't passed — or that lack a forward price — are counted as *pending*, not
scored: the BUY−AVOID spread is computed only over **resolved** verdicts.
"""

from __future__ import annotations

from datetime import date, timedelta

from mosaic.schemas.ledger import Verdict
from mosaic.schemas.market import PriceBar
from mosaic.scoring.metrics import ScoreReport, VerdictScore, aggregate, total_return
from mosaic.store import Store

_DEFAULT_COST_BPS = 25.0  # coarse small-cap one-way cost estimate (round-trip applied in metrics)
_DEFAULT_BENCHMARK_ID = "IDX-IWM"


def _close_on_or_before(bars: list[PriceBar], target: date) -> float | None:
    chosen: float | None = None
    for b in bars:  # bars come from the store ordered ascending by date
        if b.bar_date <= target:
            chosen = b.close
        else:
            break
    return chosen


def _daily_returns(bars: list[PriceBar], start: date, end: date) -> list[tuple[date, float]]:
    win = [b for b in bars if start <= b.bar_date <= end]
    out: list[tuple[date, float]] = []
    for prev, cur in zip(win, win[1:], strict=False):
        if prev.close > 0:
            out.append((cur.bar_date, cur.close / prev.close - 1.0))
    return out


def score_ledger(
    store: Store,
    *,
    as_of: date,
    cost_bps: float = _DEFAULT_COST_BPS,
    benchmark_internal_id: str = _DEFAULT_BENCHMARK_ID,
) -> tuple[list[VerdictScore], ScoreReport]:
    """Score every ledger verdict as of ``as_of``; return per-verdict scores and the aggregate."""
    bench_bars = store.get_price_history(benchmark_internal_id)
    bench_daily = dict(_daily_returns(bench_bars, date.min, as_of))

    scores: list[VerdictScore] = []
    pending = 0
    book_rets: list[float] = []
    bench_rets: list[float] = []

    for entry in store.iter_ledger():
        entry_date = entry.entry_price_as_of
        horizon_date = entry_date + timedelta(days=entry.horizon_days)
        resolved = as_of >= horizon_date
        scoring_date = min(horizon_date, as_of)

        name_bars = store.get_price_history(entry.internal_id)
        exit_price = _close_on_or_before(name_bars, scoring_date)
        bench_entry = _close_on_or_before(bench_bars, entry_date)
        bench_exit = _close_on_or_before(bench_bars, scoring_date)
        if exit_price is None or bench_entry is None or bench_exit is None:
            pending += 1  # no forward/benchmark price yet → cannot score
            continue

        score = VerdictScore(
            entry_id=entry.entry_id,
            ticker=entry.ticker,
            verdict=entry.verdict,
            resolved=resolved,
            name_return=total_return(entry.entry_price, exit_price),
            bench_return=total_return(bench_entry, bench_exit),
        )
        scores.append(score)
        # pool daily returns of resolved BUYs vs the benchmark for the beta/alpha regression
        if resolved and entry.verdict is Verdict.BUY:
            for d, r in _daily_returns(name_bars, entry_date, scoring_date):
                if d in bench_daily:
                    book_rets.append(r)
                    bench_rets.append(bench_daily[d])

    resolved_scores = [s for s in scores if s.resolved]
    pending += len([s for s in scores if not s.resolved])
    report = aggregate(
        resolved_scores,
        cost_bps=cost_bps,
        n_pending=pending,
        book_daily=book_rets or None,
        bench_daily=bench_rets or None,
    )
    return scores, report
