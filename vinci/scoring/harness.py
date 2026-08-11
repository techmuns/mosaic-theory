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
from vinci.scoring.baseline import Basket, basket_return, close_on_or_before
from vinci.scoring.metrics import ScoreReport, VerdictScore, aggregate, total_return
from vinci.store import Store

_DEFAULT_COST_BPS = 25.0  # coarse small-cap one-way cost estimate (round-trip applied in metrics)
_DEFAULT_BENCHMARK_ID = "IDX-IWM"

#: Bound to its old private name so the call sites below read unchanged. The DEFINITION moved to
#: `baseline`, because the basket must read "the price on this date" exactly as the benchmark does
#: — see that module's note on why it is shared rather than copied.
_close_on_or_before = close_on_or_before


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
    baskets: dict[str, Basket] | None = None,
) -> tuple[list[VerdictScore], ScoreReport]:
    """Score every ledger verdict as of ``as_of``; return per-verdict scores and the aggregate.

    ``baskets`` maps sleeve key → its passive comparator (see ``vinci.scoring.baseline``). Supplied
    by the caller rather than read here, because the follow list is a data-layer fact and the
    scoring package resolves neither config nor tickers — the same reason the CLI resolves a
    followed name's identity before ``log_verdict`` sees it. Absent → every sleeve's baseline
    reports "not supplied" rather than silently reading zero, and both production paths are pinned
    to supply it (``tests/test_quality_baseline.py``).
    """
    bench_bars = store.get_price_history(benchmark_internal_id)
    bench_daily = dict(_daily_returns(bench_bars, date.min, as_of))
    # Fetched ONCE per basket member, not per verdict: the windows differ per row but the series
    # does not, and a followed book re-reading three full histories per verdict would be the
    # slowest thing in the report for no gain.
    basket_bars: dict[str, dict[str, list[PriceBar]]] = {
        key: {t: store.get_price_history(iid) for t, iid in b.internal_ids.items()}
        for key, b in (baskets or {}).items()
    }

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

        # THE PASSIVE COMPARATOR, over THIS verdict's window — the counterfactual of holding the
        # whole follow list from this entry date to this scoring date instead of picking within it.
        # Computed per row (not once per sleeve) precisely because the windows differ: averaging a
        # single basket return across rows entered months apart would compare the judgement's
        # windows to a window nobody held.
        b_ret: float | None = None
        b_note: str | None = None
        sleeve_key = sleeve_of(entry)
        basket = (baskets or {}).get(sleeve_key)
        if basket is not None:
            b_ret, b_note = basket_return(
                basket, basket_bars.get(sleeve_key, {}), entry_date, scoring_date)

        score = VerdictScore(
            entry_id=entry.entry_id,
            ticker=entry.ticker,
            verdict=entry.verdict,
            resolved=resolved,
            name_return=total_return(entry.entry_price, exit_price),
            bench_return=total_return(bench_entry, bench_exit),
            basket_return=b_ret,
            basket_note=b_note,
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
        basket_labels={k: b.label for k, b in (baskets or {}).items()},
    )
    return scores, report
