"""Scoring metrics — pure math over verdict outcomes (no heavy deps; tiny-n by design).

The **primary** metric is the BUY−AVOID forward-return spread: it is benchmark-free and uses every
resolved verdict, so it directly answers "does the discriminator's verdict carry information?".
Everything else (hit-rate, excess-vs-benchmark, beta/alpha, twin-realisation) is supporting colour,
reported with the explicit caveat that the sample is tiny — these are directional gates, not
significance tests.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass

from mosaic.schemas.ledger import Verdict


def total_return(entry_price: float, exit_price: float) -> float:
    return exit_price / entry_price - 1.0


@dataclass(frozen=True)
class VerdictScore:
    """One verdict's outcome at the scoring date (resolved at horizon, or an interim mark)."""

    entry_id: str
    ticker: str
    verdict: Verdict
    resolved: bool  # True once the thesis horizon has passed
    name_return: float
    bench_return: float

    @property
    def excess_gross(self) -> float:
        return self.name_return - self.bench_return

    def excess_net(self, cost_bps: float) -> float:
        # round-trip cost in return terms (entry + exit); coarse, applied to the long leg.
        return self.excess_gross - 2.0 * cost_bps / 10_000.0


def ols_beta_alpha(
    book_returns: list[float], bench_returns: list[float]
) -> tuple[float | None, float | None]:
    """Single-factor beta/alpha of a return series vs the benchmark (β=cov/var, α=mean−β·mean).

    The benchmark is a small-cap index, so β captures small-cap exposure and α is the residual
    ("is it all beta?"). A full Fama-French 3-factor decomposition is a later enhancement. Returns
    (None, None) when there is too little data to estimate.
    """
    n = len(book_returns)
    if n < 3 or len(bench_returns) != n:
        return None, None
    mb = statistics.fmean(book_returns)
    mm = statistics.fmean(bench_returns)
    var = sum((m - mm) ** 2 for m in bench_returns) / n
    if var == 0:
        return None, None
    cov = sum((b - mb) * (m - mm) for b, m in zip(book_returns, bench_returns, strict=True)) / n
    beta = cov / var
    alpha = mb - beta * mm
    return beta, alpha


@dataclass(frozen=True)
class ScoreReport:
    """Aggregate scoring over the resolved verdicts, plus the count still pending."""

    n_resolved_buy: int
    n_resolved_avoid: int
    n_pending: int
    buy_mean_return: float | None
    avoid_mean_return: float | None
    buy_avoid_spread: float | None  # PRIMARY
    buy_hit_rate: float | None  # fraction of BUYs that beat the benchmark
    avoid_hit_rate: float | None  # fraction of AVOIDs that lagged the benchmark
    buy_excess_gross: float | None
    buy_excess_net: float | None
    beta: float | None
    alpha: float | None
    twin_buy_bounced: bool | None  # did BUYs on average rise?
    twin_avoid_fell: bool | None  # did AVOID-terminal names on average keep falling?

    def to_dict(self) -> dict[str, object]:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}

    def to_markdown(self) -> str:
        def pct(x: float | None) -> str:
            return "n/a" if x is None else f"{x:+.1%}"

        lines = [
            "# Loop 1 — scoring report (paper mode)",
            "",
            f"- Resolved verdicts: **{self.n_resolved_buy} BUY**, "
            f"**{self.n_resolved_avoid} AVOID** ({self.n_pending} pending)",
            f"- **BUY−AVOID spread (primary): {pct(self.buy_avoid_spread)}**",
            f"- BUY mean return {pct(self.buy_mean_return)} · AVOID mean return "
            f"{pct(self.avoid_mean_return)}",
            f"- Hit-rate — BUY beat benchmark: {pct(self.buy_hit_rate)} · "
            f"AVOID lagged benchmark: {pct(self.avoid_hit_rate)}",
            f"- BUY excess vs benchmark — gross {pct(self.buy_excess_gross)} · "
            f"net {pct(self.buy_excess_net)}",
            f"- BUY book β vs benchmark: "
            f"{'n/a' if self.beta is None else f'{self.beta:.2f}'} · "
            f"α: {pct(self.alpha)}",
            f"- Twin-realisation — BUYs bounced: {self.twin_buy_bounced} · "
            f"AVOIDs kept falling: {self.twin_avoid_fell}",
            "",
            "_Tiny n: directional gates, not significance tests. Paper fills are optimistic._",
        ]
        return "\n".join(lines)


def aggregate(
    scores: list[VerdictScore],
    *,
    cost_bps: float,
    n_pending: int,
    book_daily: list[float] | None = None,
    bench_daily: list[float] | None = None,
) -> ScoreReport:
    """Aggregate per-verdict scores into the report. ``*_daily`` feed the beta/alpha regression."""
    buys = [s for s in scores if s.verdict is Verdict.BUY]
    avoids = [s for s in scores if s.verdict is Verdict.AVOID_TERMINAL]

    def mean(xs: list[float]) -> float | None:
        return statistics.fmean(xs) if xs else None

    def frac(flags: list[bool]) -> float | None:
        return sum(flags) / len(flags) if flags else None

    buy_mean = mean([s.name_return for s in buys])
    avoid_mean = mean([s.name_return for s in avoids])
    spread = buy_mean - avoid_mean if buy_mean is not None and avoid_mean is not None else None
    beta = alpha = None
    if book_daily is not None and bench_daily is not None:
        beta, alpha = ols_beta_alpha(book_daily, bench_daily)

    return ScoreReport(
        n_resolved_buy=len(buys),
        n_resolved_avoid=len(avoids),
        n_pending=n_pending,
        buy_mean_return=buy_mean,
        avoid_mean_return=avoid_mean,
        buy_avoid_spread=spread,
        buy_hit_rate=frac([s.excess_gross > 0 for s in buys]),
        avoid_hit_rate=frac([s.excess_gross < 0 for s in avoids]),
        buy_excess_gross=mean([s.excess_gross for s in buys]),
        buy_excess_net=mean([s.excess_net(cost_bps) for s in buys]),
        beta=beta,
        alpha=alpha,
        twin_buy_bounced=(buy_mean > 0) if buy_mean is not None else None,
        twin_avoid_fell=(avoid_mean < 0) if avoid_mean is not None else None,
    )
