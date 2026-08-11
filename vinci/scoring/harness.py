"""Scoring harness — score the decision ledger against stored forward EOD prices.

For each verdict it computes the name's return from the **frozen entry price** to the scoring date
(the thesis horizon once it has passed, else an interim mark) and the benchmark's return over the
same window, then aggregates the resolved verdicts into the report (see ``vinci.scoring.metrics``).
Verdicts whose horizon hasn't passed — or that lack a forward price — are counted as *pending*, not
scored: the BUY−AVOID spread is computed only over **resolved** verdicts.
"""

from __future__ import annotations

from datetime import date, timedelta

from vinci.schemas.ledger import (
    EVENT_CLOSE,
    ORIGIN_SCREEN,
    Verdict,
    origin_of,
    sleeve_of,
)
from vinci.schemas.market import PriceBar
from vinci.scoring.metrics import ScoreReport, VerdictScore, aggregate, total_return
from vinci.store import Store

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
        # A CLOSE IS NOT A DECISION. A close row is appended (never an edit) and carries the
        # ORIGINAL verdict for provenance, so partitioning by verdict counts that name's leg
        # TWICE — `monitor.decision_rows` has filtered these since 2026-07-22 for exactly this
        # reason, and this loop, which partitions the same way, did not. The committed ledger
        # already holds two closes against four decisions; it cost nothing only because nothing
        # has resolved yet. Filtered here rather than inside `aggregate`, so a close never reaches
        # `scores` either — the per-verdict listing the report renders would otherwise show a
        # phantom row that the counts alone would not reveal.
        if entry.event == EVENT_CLOSE:
            continue
        entry_date = entry.entry_price_as_of
        horizon_date = entry_date + timedelta(days=entry.horizon_days)
        resolved = as_of >= horizon_date
        scoring_date = min(horizon_date, as_of)

        name_bars = store.get_price_history(entry.internal_id)
        exit_price = _close_on_or_before(name_bars, scoring_date)
        bench_entry = _close_on_or_before(bench_bars, entry_date)
        bench_exit = _close_on_or_before(bench_bars, scoring_date)
        if exit_price is None or bench_entry is None or bench_exit is None:
            # No forward/benchmark price yet → cannot score. SCOPED HERE TOO, and this is the
            # easier half to miss: the row never reaches ``scores``, so the origin filter below
            # can never see it. A followed name whose bars are not loaded yet would land in the
            # screen-only pending count through this branch alone — the one path that skips
            # every later filter by construction (review #382).
            if origin_of(entry) == ORIGIN_SCREEN:
                pending += 1
            continue

        score = VerdictScore(
            entry_id=entry.entry_id,
            ticker=entry.ticker,
            verdict=entry.verdict,
            resolved=resolved,
            name_return=total_return(entry.entry_price, exit_price),
            bench_return=total_return(bench_entry, bench_exit),
            sector=entry.sector,  # carried through for the per-sector spread read
            machine_proposal=entry.machine_proposal,  # sealed at log time (2026-07-13 pivot)
            disposition=entry.disposition,
            # READ THROUGH THE HELPERS, never off the attribute: a legacy row carries None for
            # both, and its truthful reading is screen/overshoot (no other route could reach the
            # ledger when it was written). One definition, so the report cannot disagree with it.
            origin=origin_of(entry),
            sleeve=sleeve_of(entry),
        )
        scores.append(score)
        # pool daily returns of resolved BUYs vs the benchmark for the beta/alpha regression.
        # SCREEN-ORIGIN ONLY, matching the primary spread this beta/alpha is printed BESIDE
        # (review #378): the report puts them under the same screen-scoped heading, so a followed
        # quality BUY pooling its daily returns in here would move a number the reader takes to
        # describe the overshoot book. The scope claim has to hold for every primary input, not
        # just for the spread itself.
        if resolved and entry.verdict is Verdict.BUY and origin_of(entry) == ORIGIN_SCREEN:
            for d, r in _daily_returns(name_bars, entry_date, scoring_date):
                if d in bench_daily:
                    book_rets.append(r)
                    bench_rets.append(bench_daily[d])

    resolved_scores = [s for s in scores if s.resolved]
    # PENDING IS A PRIMARY-REPORT FIGURE and is scoped the same way, for the same reason: it is
    # rendered on the line above the screen-only resolved counts, so a followed pending row would
    # inflate a count the reader reads as the overshoot book's. Per-book pending belongs with the
    # per-sleeve curves when there is a followed row to count.
    pending += len([s for s in scores if not s.resolved and s.origin == ORIGIN_SCREEN])
    report = aggregate(
        resolved_scores,
        cost_bps=cost_bps,
        n_pending=pending,
        book_daily=book_rets or None,
        bench_daily=bench_rets or None,
    )
    return scores, report
