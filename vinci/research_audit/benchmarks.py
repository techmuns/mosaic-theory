"""Benchmarks — the two CIQ index series from the workbook, and Polygon ETF total-return PROXIES.

LABELS ARE LOAD-BEARING. An index level read from the CIQ export is ``kind="INDEX"``; an ETF's
total-return series is ``kind="PROXY"`` and is never called by the index's name — SPY is "SPY TR
(PROXY for the S&P 500)", never "S&P 500 Total Return". A proxy's tracking difference against its
index is MEASURED here when the index series exists, and stated as unmeasured when it does not.

CURRENCY. The CIQ export does not print the MSCI World series' currency (the workbook flags it
"USD unconfirmed"). ``tracking_difference`` against URTH — a USD-denominated MSCI World ETF —
tests it: a local-currency series would open a gap of several points against URTH whenever the
dollar moves hard (H1 2025 is such a window), a USD series would not.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from datetime import date

from vinci.research_audit.prices import Series
from vinci.research_audit.workbook import AuditWorkbook


@dataclass(frozen=True)
class Benchmark:
    code: str
    label: str
    kind: str  # "INDEX" | "PROXY"
    levels: dict[date, float]
    source: str

    def ret(self, a: date, b: date) -> float | None:
        la, lb = self.levels.get(a), self.levels.get(b)
        if la is None or lb is None or la == 0:
            return None
        return lb / la - 1.0


def ciq_benchmarks(wb: AuditWorkbook) -> tuple[Benchmark, Benchmark]:
    """CIQ chart % → rebased level ``100 * (1 + pct)`` — the workbook's own F/G-column formula."""
    msci = {r.day: 100.0 * (1.0 + r.msci_world_net) for r in wb.ciq_daily
            if r.msci_world_net is not None}
    spx = {r.day: 100.0 * (1.0 + r.sp500_net) for r in wb.ciq_daily if r.sp500_net is not None}
    src = (f"S&P Capital IQ Chart Builder export '{wb.ciq_index_export}' as transcribed in the "
           f"workbook's 'CIQ Daily Data' sheet (cumulative chart %, 0.01pp rounding)")
    return (
        Benchmark("MSCI_WORLD_NET_CIQ", "MSCI World Net Return Index (CIQ export)", "INDEX",
                  msci, src + ", column C"),
        Benchmark("SP500_NET_CIQ", "S&P 500 Net Total Return Index (CIQ export)", "INDEX",
                  spx, src + ", column B"),
    )


def proxy_benchmark(series: Series, label: str) -> Benchmark:
    return Benchmark(
        code=f"{series.symbol}_TR_PROXY", label=f"{series.symbol} total return (PROXY for {label})",
        kind="PROXY", levels={p.day: p.adj_close for p in series.points},
        source=(f"Polygon {series.symbol}: raw closes + Polygon cash distributions reinvested at "
                f"ex-date close (vinci.research_audit.prices)"),
    )


@dataclass(frozen=True)
class TrackingReport:
    proxy: str
    index: str
    first: date
    last: date
    n_common: int
    proxy_total: float
    index_total: float
    annualized_diff: float  # proxy minus index, per year
    daily_te_annualized: float
    by_year: list[tuple[str, float, float]]  # (period, proxy return, index return)
    windows: list[tuple[str, float, float]]


def _ret(levels: dict[date, float], a: date, b: date) -> float:
    return levels[b] / levels[a] - 1.0


def tracking_difference(proxy: Benchmark, index: Benchmark,
                        windows: list[tuple[str, date, date]] | None = None) -> TrackingReport:
    common = sorted(set(proxy.levels) & set(index.levels))
    if len(common) < 20:
        raise ValueError(f"{proxy.code} vs {index.code}: only {len(common)} common dates")
    a, b = common[0], common[-1]
    pt, it = _ret(proxy.levels, a, b), _ret(index.levels, a, b)
    years = (b - a).days / 365.25
    diffs = [
        (proxy.levels[d1] / proxy.levels[d0] - 1.0) - (index.levels[d1] / index.levels[d0] - 1.0)
        for d0, d1 in zip(common, common[1:], strict=False)
    ]
    te = statistics.pstdev(diffs) * math.sqrt(252) if len(diffs) > 1 else float("nan")
    by_year: list[tuple[str, float, float]] = []
    for y in sorted({d.year for d in common}):
        ys = [d for d in common if d.year == y]
        prev = [d for d in common if d.year < y]
        start = prev[-1] if prev else ys[0]
        by_year.append((f"{start}→{ys[-1]}", _ret(proxy.levels, start, ys[-1]),
                        _ret(index.levels, start, ys[-1])))
    wins: list[tuple[str, float, float]] = []
    for name, w0, w1 in windows or []:
        cs = [d for d in common if w0 <= d <= w1]
        if len(cs) >= 2:
            wins.append((f"{name} {cs[0]}→{cs[-1]}", _ret(proxy.levels, cs[0], cs[-1]),
                         _ret(index.levels, cs[0], cs[-1])))
    return TrackingReport(
        proxy=proxy.label, index=index.label, first=a, last=b, n_common=len(common),
        proxy_total=pt, index_total=it,
        annualized_diff=(1 + pt) ** (1 / years) - (1 + it) ** (1 / years),
        daily_te_annualized=te, by_year=by_year, windows=wins,
    )


# --- currency of the CIQ MSCI World series ----------------------------------------------------

@dataclass(frozen=True)
class CurrencyFit:
    hypothesis: str  # "USD (as exported)" or the FX pair used to convert into USD
    first: date
    last: date
    n_common: int
    proxy_total: float
    converted_total: float
    annualized_diff: float
    rms_21_session_gap: float


def _to_usd(level: float, pair: str, rate: float) -> float:
    """C:XXXUSD quotes USD per XXX (multiply); C:USDXXX quotes XXX per USD (divide)."""
    return level * rate if pair.endswith("USD") and not pair.startswith("C:USD") else level / rate


def currency_fit(ciq: Benchmark, usd_proxy: Benchmark,
                 fx: dict[str, dict[date, float]]) -> list[CurrencyFit]:
    """For each hypothesis, convert the CIQ series into USD and measure how closely it tracks a
    USD-denominated proxy of the same index. The right currency is the one that leaves only the
    ETF's own small tracking residue; a wrong one leaves the currency's moves in the gap."""
    hyps: list[tuple[str, dict[date, float]]] = [("USD (as exported)", dict(ciq.levels))]
    for pair, rates in sorted(fx.items()):
        hyps.append((pair, {d: _to_usd(v, pair, rates[d]) for d, v in ciq.levels.items()
                            if d in rates}))
    common_all = set(usd_proxy.levels)
    for _, conv in hyps[1:]:
        common_all &= set(conv)
    common = sorted(common_all & set(ciq.levels))
    out: list[CurrencyFit] = []
    for name, conv in hyps:
        a, b = common[0], common[-1]
        pt, ct = _ret(usd_proxy.levels, a, b), _ret(conv, a, b)
        years = (b - a).days / 365.25
        gaps = [_ret(usd_proxy.levels, common[i], common[i + 21]) - _ret(conv, common[i],
                                                                          common[i + 21])
                for i in range(0, len(common) - 21, 21)]
        out.append(CurrencyFit(
            hypothesis=name, first=a, last=b, n_common=len(common), proxy_total=pt,
            converted_total=ct, annualized_diff=(1 + pt) ** (1 / years) - (1 + ct) ** (1 / years),
            rms_21_session_gap=math.sqrt(statistics.fmean(g * g for g in gaps)),
        ))
    return sorted(out, key=lambda c: c.rms_21_session_gap)


def converted_benchmark(ciq: Benchmark, pair: str, rates: dict[date, float]) -> Benchmark:
    """The CIQ series converted to USD with Polygon FX closes — DERIVED, for measuring a USD
    proxy's tracking difference only (Polygon's FX close is not MSCI's 4pm London fixing)."""
    return Benchmark(
        code=f"MSCI_WORLD_NET_CIQ_x_{pair.replace('C:', '')}_DERIVED",
        label=f"MSCI World Net (CIQ series converted to USD with Polygon {pair}) — DERIVED",
        kind="DERIVED",
        levels={d: _to_usd(v, pair, rates[d]) for d, v in ciq.levels.items() if d in rates},
        source=ciq.source + f"; converted with Polygon {pair} daily close",
    )
