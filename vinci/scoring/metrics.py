"""Scoring metrics — pure math over verdict outcomes (no heavy deps; tiny-n by design).

The **primary** metric is the BUY−AVOID forward-return spread: it is benchmark-free and uses every
resolved verdict, so it directly answers "does the discriminator's verdict carry information?".
Everything else (hit-rate, excess-vs-benchmark, beta/alpha, twin-realisation) is supporting colour,
reported with the explicit caveat that the sample is tiny — these are directional gates, not
significance tests.
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from dataclasses import dataclass, field

from vinci.schemas.ledger import ORIGIN_SCREEN, Disposition, Verdict
from vinci.sleeves import DEFAULT_SLEEVE


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
    sector: str | None = None  # carried from the ledger entry — for the per-sector spread read
    # Sealed machine proposal + disposition (2026-07-13 pivot) — carried from the ledger entry so
    # the report can read the machine curve and the override subset. None == pre-pivot entry.
    machine_proposal: Verdict | None = None
    disposition: Disposition | None = None
    # WHICH BOOK, and HOW the name got in — carried from the ledger row so the report can segment.
    # Defaults are the truthful reading of a row logged before the fields existed: the screen was
    # the only route that could reach the ledger, and overshoot the only strategy.
    origin: str = ORIGIN_SCREEN
    sleeve: str = DEFAULT_SLEEVE

    @property
    def excess_gross(self) -> float:
        return self.name_return - self.bench_return

    def excess_net(self, cost_bps: float) -> float:
        # round-trip cost in return terms (entry + exit); coarse, applied to the long leg.
        return self.excess_gross - 2.0 * cost_bps / 10_000.0


@dataclass(frozen=True)
class SectorSpread:
    """The BUY−AVOID spread within ONE sector — None/insufficient until both legs have enough."""

    sector: str
    n_buy: int
    n_avoid: int
    spread: float | None  # None until >= min_per_leg resolved BUYs AND AVOIDs in this sector
    sufficient: bool  # False == "insufficient data" — honest until the per-sector sample is real


def spread_by_sector(
    scores: list[VerdictScore], *, min_per_leg: int = 2
) -> dict[str, SectorSpread]:
    """Per-sector BUY−AVOID spread over the given (resolved) verdict scores. A sector reports
    ``sufficient=False`` ("insufficient data") until it has at least ``min_per_leg`` resolved BUYs
    AND AVOIDs — the per-sector edge is only readable once each sector's sample is real. Untagged
    verdicts (``sector is None``, e.g. the pre-feature VRRM entry) bucket under ``"Unknown"``.

    SCREEN-ORIGIN ONLY, because this is a CUT OF THE PRIMARY SPREAD and has to mean the same thing
    it does. It also closes the same silent drop the per-sleeve curves close: the legs below match
    ``AVOID_TERMINAL`` by IDENTITY, so a ``PASS`` row would land in neither leg and disappear from
    its sector with nothing raised. Filtering by origin is the honest fix rather than widening the
    labels — a quality verdict does not belong in a per-sector read of the overshoot
    discriminator in the first place."""
    by: dict[str, list[VerdictScore]] = defaultdict(list)
    for s in scores:
        if s.origin != ORIGIN_SCREEN:
            continue
        by[s.sector or "Unknown"].append(s)
    out: dict[str, SectorSpread] = {}
    for sector, ss in sorted(by.items()):
        buys = [x.name_return for x in ss if x.verdict is Verdict.BUY]
        avoids = [x.name_return for x in ss if x.verdict is Verdict.AVOID_TERMINAL]
        sufficient = len(buys) >= min_per_leg and len(avoids) >= min_per_leg
        spread = (statistics.fmean(buys) - statistics.fmean(avoids)) if sufficient else None
        out[sector] = SectorSpread(sector, len(buys), len(avoids), spread, sufficient)
    return out


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
class SleeveSpread:
    """One strategy book's own curve — its long leg minus the leg it is measured against.

    SEPARATE FROM THE PRIMARY by construction: `overshoot` here is the screen-origin book and
    reproduces the primary number, while `quality` accumulates its own BUY−PASS curve. Pooling them
    would answer a question nobody asked — the fund's proof is per-book, which is also what an
    allocator asks for (one composite per strategy)."""

    sleeve: str
    n_long: int
    n_short: int          # the "measured against" leg (AVOID_TERMINAL, PASS, …) — never a short
    long_mean: float | None
    short_mean: float | None
    spread: float | None  # None (never 0.0) when either leg is empty — an empty leg is not a zero


@dataclass(frozen=True)
class OverrideOutcome:
    """One resolved OVERRIDE — human vs machine on the same name, with the forward outcome.
    The most informative subset the pivot produces: it directly reads which side the forward
    return vindicated. Reported raw (ticker · both calls · return); the human reads it."""

    ticker: str
    human: Verdict
    machine: Verdict
    name_return: float


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
    # Per-sector BUY−AVOID spread (the sector-expertise read) — each "insufficient data" until its
    # own sample is real. Empty until verdicts resolve. See STATE.md §sector-expertise scoping.
    by_sector: dict[str, SectorSpread] = field(default_factory=dict)
    # --- machine-proposal shadow curves (2026-07-13 pivot) -------------------------------------
    # The HUMAN-final spread above stays the PRIMARY metric; these read the machine's sealed
    # proposals and the confirm/override dispositions over the SAME resolved verdicts, so the
    # decomposition (machine baseline vs human delta) accumulates from day one.
    n_machine_buy: int = 0
    n_machine_avoid: int = 0
    machine_buy_avoid_spread: float | None = None
    n_confirmed: int = 0
    n_overridden: int = 0
    n_no_proposal: int = 0
    overrides: tuple[OverrideOutcome, ...] = ()
    # PER-BOOK curves, beside the primary and never inside it (STATE.md §4 SLEEVE ARCHITECTURE).
    by_sleeve: dict[str, SleeveSpread] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        d: dict[str, object] = {k: getattr(self, k) for k in self.__dataclass_fields__}
        d["by_sector"] = {
            s: {"n_buy": v.n_buy, "n_avoid": v.n_avoid, "spread": v.spread,
                "sufficient": v.sufficient}
            for s, v in self.by_sector.items()
        }
        d["by_sleeve"] = {
            k: {"n_long": v.n_long, "n_short": v.n_short, "long_mean": v.long_mean,
                "short_mean": v.short_mean, "spread": v.spread}
            for k, v in self.by_sleeve.items()
        }
        d["overrides"] = [
            {"ticker": o.ticker, "human": o.human.value, "machine": o.machine.value,
             "name_return": o.name_return}
            for o in self.overrides
        ]
        return d

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
        ]
        sector_lines = [
            f"- {v.sector}: {('spread ' + pct(v.spread)) if v.sufficient else 'insufficient data'} "
            f"({v.n_buy} buy / {v.n_avoid} avoid)"
            for v in self.by_sector.values()
        ]
        lines += [
            "",
            "## Per-sector BUY−AVOID spread (sector-expertise read)",
            *(sector_lines or ["- (no resolved verdicts yet)"]),
        ]
        override_lines = [
            f"- {o.ticker}: human {o.human.value} vs machine {o.machine.value} → "
            f"name return {pct(o.name_return)}"
            for o in self.overrides
        ]
        lines += [
            "",
            "## Machine-proposal shadow curves (2026-07-13 pivot)",
            "_The human-final spread above stays PRIMARY; this decomposes it into the machine's_ "
            "_sealed-proposal baseline and the human's confirm/override delta._",
            f"- Machine BUY−AVOID spread: {pct(self.machine_buy_avoid_spread)} "
            f"({self.n_machine_buy} machine-BUY / {self.n_machine_avoid} machine-AVOID resolved)",
            f"- Dispositions (resolved): confirmed {self.n_confirmed} · "
            f"overridden {self.n_overridden} · no-proposal {self.n_no_proposal}",
            *(override_lines or ["- (no resolved overrides yet)"]),
            "",
            "_Tiny n: directional gates, not significance tests. Paper fills are optimistic._",
        ]
        return "\n".join(lines)


def spread_by_sleeve(scores: list[VerdictScore]) -> dict[str, SleeveSpread]:
    """Each strategy book's own curve, with ITS OWN leg labels read from the registry.

    THE LEG LABELS ARE NOT HARDCODED, and that is the point of the registry: overshoot measures
    BUY−AVOID_TERMINAL while quality measures BUY−PASS, so a hardcoded `AVOID_TERMINAL` filter
    would silently drop every quality row out of both legs and report an empty curve as though the
    book had no verdicts. `Sleeve.verdicts` names (long, measured-against) per book, so adding
    sleeve N+1 needs no change here at all.

    A verdict whose label belongs to NEITHER leg of its own sleeve is counted in `n_long`/`n_short`
    by nobody and would vanish silently — so it raises. That is the exact failure mode the
    exact-identity filters had before this existed.
    """
    from vinci.sleeves import BY_KEY

    out: dict[str, SleeveSpread] = {}
    for key in sorted({s.sleeve for s in scores}):
        rows = [s for s in scores if s.sleeve == key]
        row = BY_KEY.get(key)
        if row is None:                       # validated at every write path; belt-and-braces here
            raise ValueError(f"scored rows carry sleeve {key!r}, which no registry row defines")
        long_label, short_label = row.verdicts
        longs = [r.name_return for r in rows if r.verdict.value == long_label]
        shorts = [r.name_return for r in rows if r.verdict.value == short_label]
        unclassified = [r for r in rows if r.verdict.value not in (long_label, short_label)]
        if unclassified:
            raise ValueError(
                f"sleeve {key!r} scored {len(unclassified)} verdict(s) belonging to neither of its "
                f"legs ({long_label}/{short_label}): "
                f"{sorted({r.verdict.value for r in unclassified})} — such a row would fall out of "
                f"the curve without appearing anywhere, which is the silent-drop this refuses")
        lm = statistics.fmean(longs) if longs else None
        sm = statistics.fmean(shorts) if shorts else None
        out[key] = SleeveSpread(
            sleeve=key, n_long=len(longs), n_short=len(shorts), long_mean=lm, short_mean=sm,
            spread=(lm - sm if lm is not None and sm is not None else None))
    return out


def aggregate(
    scores: list[VerdictScore],
    *,
    cost_bps: float,
    n_pending: int,
    book_daily: list[float] | None = None,
    bench_daily: list[float] | None = None,
) -> ScoreReport:
    """Aggregate per-verdict scores into the report. ``*_daily`` feed the beta/alpha regression."""
    # THE PRIMARY SPREAD IS SCREEN-ORIGIN ONLY (operator decision 2026-08-07). The spread is the
    # fund's proof and it measures the discriminator ON the $300M–$10B hunting ground; pooling
    # followed megacap verdicts into it would silently change what the number means. Every other
    # cut accumulates beside it in `by_sleeve`, never inside this one.
    primary = [s for s in scores if s.origin == ORIGIN_SCREEN]
    buys = [s for s in primary if s.verdict is Verdict.BUY]
    avoids = [s for s in primary if s.verdict is Verdict.AVOID_TERMINAL]

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

    # machine shadow curves (2026-07-13 pivot) — bucketed by the SEALED machine proposal; the
    # override subset carries each disagreement's forward outcome raw.
    # THE SAME SET THE PRIMARY MEASURES (`primary`, not `scores`), because this curve exists to be
    # COMPARED with the primary: the pivot's whole question is how the human's spread differs from
    # the machine's ON THE SAME NAMES. Reading a wider set would make the two incomparable while
    # still printing them side by side — and it would silently drop a PASS proposal, which matches
    # neither identity filter below.
    m_buys = [s.name_return for s in primary if s.machine_proposal is Verdict.BUY]
    m_avoids = [s.name_return for s in primary if s.machine_proposal is Verdict.AVOID_TERMINAL]
    m_buy_mean, m_avoid_mean = mean(m_buys), mean(m_avoids)
    machine_spread = (
        m_buy_mean - m_avoid_mean
        if m_buy_mean is not None and m_avoid_mean is not None else None
    )
    # DELIBERATELY OVER `scores`, NOT `primary` — the one place the wider set is right. This is the
    # disagreement LOG, not a curve: every override is decision-relevant evidence about the
    # human-vs-machine relationship regardless of which book the name sits in, and dropping the
    # followed ones would hide exactly the overrides most worth reading. It is a list of named
    # rows, so nothing here is pooled into a number that would change meaning.
    overrides = tuple(
        OverrideOutcome(s.ticker, s.verdict, s.machine_proposal, s.name_return)
        for s in scores
        if s.disposition is Disposition.OVERRIDDEN and s.machine_proposal is not None
    )

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
        by_sector=spread_by_sector(scores),
        by_sleeve=spread_by_sleeve(scores),
        n_machine_buy=len(m_buys),
        n_machine_avoid=len(m_avoids),
        machine_buy_avoid_spread=machine_spread,
        n_confirmed=sum(1 for s in scores if s.disposition is Disposition.CONFIRMED),
        n_overridden=sum(1 for s in scores if s.disposition is Disposition.OVERRIDDEN),
        n_no_proposal=sum(1 for s in scores if s.disposition is Disposition.NO_PROPOSAL),
        overrides=overrides,
    )
