"""Step 7 verification — the scoring harness.

The math is tested deterministically (returns, OLS beta/alpha, aggregation) and end-to-end on a
**backfilled** ledger with known forward prices. Per the runbook this tests the *arithmetic only* —
historical outcomes are not evidence of edge (the discriminator validates **forward**).
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import pytest

from mosaic.schemas.ledger import Confidence, LedgerEntry, Verdict
from mosaic.schemas.market import PriceBar
from mosaic.scoring import aggregate, ols_beta_alpha, score_ledger, total_return
from mosaic.scoring.metrics import VerdictScore
from mosaic.store import Store


def test_total_return() -> None:
    assert total_return(100.0, 130.0) == pytest.approx(0.30)
    assert total_return(50.0, 40.0) == pytest.approx(-0.20)


def test_ols_beta_alpha_recovers_known_beta() -> None:
    bench = [0.01, -0.02, 0.03, 0.00, -0.01, 0.015]
    book = [2 * x for x in bench]  # beta 2, alpha 0
    beta, alpha = ols_beta_alpha(book, bench)
    assert beta == pytest.approx(2.0)
    assert alpha == pytest.approx(0.0, abs=1e-9)


def test_ols_insufficient_data() -> None:
    assert ols_beta_alpha([0.01], [0.01]) == (None, None)


def _vs(ticker: str, verdict: Verdict, name_ret: float, bench_ret: float) -> VerdictScore:
    return VerdictScore(
        entry_id=f"V-{ticker}", ticker=ticker, verdict=verdict, resolved=True,
        name_return=name_ret, bench_return=bench_ret,
    )


def test_aggregate_spread_hitrate_twin() -> None:
    scores = [
        _vs("AAA", Verdict.BUY, 0.20, 0.05),  # beat bench
        _vs("BBB", Verdict.BUY, 0.10, 0.05),  # beat bench
        _vs("CCC", Verdict.AVOID_TERMINAL, -0.30, 0.05),  # lagged bench (good AVOID)
    ]
    r = aggregate(scores, cost_bps=25.0, n_pending=2)
    assert r.buy_mean_return == pytest.approx(0.15)
    assert r.avoid_mean_return == pytest.approx(-0.30)
    assert r.buy_avoid_spread == pytest.approx(0.45)  # PRIMARY: 0.15 − (−0.30)
    assert r.buy_hit_rate == pytest.approx(1.0)  # both BUYs beat bench
    assert r.avoid_hit_rate == pytest.approx(1.0)  # AVOID lagged bench
    assert r.buy_excess_gross == pytest.approx(0.15 - 0.05)
    assert r.buy_excess_net == pytest.approx(0.10 - 2 * 25 / 10_000)  # round-trip cost
    assert r.twin_buy_bounced is True and r.twin_avoid_fell is True
    assert r.n_pending == 2


def _bars(iid: str, points: list[tuple[date, float]]) -> list[PriceBar]:
    return [
        PriceBar(internal_id=iid, bar_date=d, open=c, high=c + 1, low=c - 1, close=c,
                 volume=1e6, source="t")
        for d, c in points
    ]


def _entry(
    ticker: str, iid: str, verdict: Verdict, entry_price: float, entry_date: date
) -> LedgerEntry:
    return LedgerEntry(
        entry_id=f"V-{ticker}", candidate_id=f"{ticker}-screen2", internal_id=iid, ticker=ticker,
        verdict=verdict, twin_call="t", entry_price=entry_price, entry_price_as_of=entry_date,
        thesis="t", kill_criteria="k", horizon_days=90, confidence=Confidence.MEDIUM,
        decided_at=datetime.combine(entry_date, datetime.min.time()),
    )


def test_score_ledger_backfilled_math_only(tmp_path: Path) -> None:
    entry_d, exit_d = date(2025, 1, 15), date(2025, 4, 15)  # 90-day horizon
    with Store(tmp_path / "s.db") as store:
        # benchmark IWM: +5% over the window
        store.write_prices(_bars("IDX-IWM", [(entry_d, 100.0), (exit_d, 105.0)]))
        # a BUY that rose +30% and an AVOID-terminal that fell -20%
        store.write_prices(_bars("SEC-A", [(entry_d, 100.0), (exit_d, 130.0)]))
        store.write_prices(_bars("SEC-B", [(entry_d, 50.0), (exit_d, 40.0)]))
        store.append_ledger(_entry("AAA", "SEC-A", Verdict.BUY, 100.0, entry_d))
        store.append_ledger(_entry("BBB", "SEC-B", Verdict.AVOID_TERMINAL, 50.0, entry_d))

        scores, report = score_ledger(store, as_of=date(2025, 5, 1), cost_bps=25.0)

    assert {s.ticker: round(s.name_return, 4) for s in scores} == {"AAA": 0.30, "BBB": -0.20}
    assert all(s.resolved for s in scores)  # horizon passed by the as-of date
    assert report.buy_avoid_spread == pytest.approx(0.50)  # +0.30 − (−0.20)
    assert report.buy_hit_rate == pytest.approx(1.0)  # BUY beat the +5% benchmark
    assert report.avoid_hit_rate == pytest.approx(1.0)  # AVOID lagged it
    assert report.twin_buy_bounced is True and report.twin_avoid_fell is True


def test_score_ledger_pending_when_horizon_not_reached(tmp_path: Path) -> None:
    entry_d = date(2026, 6, 1)
    with Store(tmp_path / "s.db") as store:
        store.write_prices(_bars("IDX-IWM", [(entry_d, 100.0), (date(2026, 6, 10), 101.0)]))
        store.write_prices(_bars("SEC-A", [(entry_d, 100.0), (date(2026, 6, 10), 90.0)]))
        store.append_ledger(_entry("AAA", "SEC-A", Verdict.BUY, 100.0, entry_d))
        # as-of is well before entry+90d -> unresolved -> pending, not scored
        _scores, report = score_ledger(store, as_of=date(2026, 6, 10))
    assert report.n_resolved_buy == 0
    assert report.n_pending == 1
    assert report.buy_avoid_spread is None
