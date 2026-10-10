"""Validation — reproduce the CIQ pilot (AXP / BKR, MS-01) from Polygon and explain every gap.

Three checks, each answering a different question:
1. ``ciq_pilot_arithmetic`` — does the workbook's stored pilot result follow from its own CIQ daily
   rows? (Workbook self-consistency; the CIQ inputs are taken as given.)
2. ``pilot_vs_polygon`` — does an independent Polygon total-return series give the same 6/9/12m
   result on the same entry/exit sessions and the same benchmark? A difference beyond
   ``MATERIAL_PP`` is MATERIAL and is investigated before the wider universe is trusted.
3. ``path_diagnostics`` — over the whole common window, does CIQ's "Dividend Adj" path track a
   dividends-reinvested series or a price-only one, and where (which ex-dates) do they part?
"""

from __future__ import annotations

import math
import statistics
from datetime import date
from typing import Any

from vinci.research_audit.engine import Obs
from vinci.research_audit.prices import Series
from vinci.research_audit.workbook import AuditWorkbook, CiqDailyRow

#: A horizon return gap (percentage points) above this is MATERIAL. CIQ chart values carry 0.01pp
#: rounding (≈0.01pp of error per endpoint), so anything near 0.5pp is a method difference.
MATERIAL_PP = 0.50

_CIQ_COL = {"AXP": "axp_div_adj", "BKR": "bkr_div_adj"}


def _ciq_level(r: CiqDailyRow, attr: str) -> float | None:
    v = getattr(r, attr)
    return None if v is None else 100.0 * (1.0 + float(v))


def ciq_pilot_arithmetic(wb: AuditWorkbook) -> list[dict[str, Any]]:
    by_day = {r.day: r for r in wb.ciq_daily}
    out: list[dict[str, Any]] = []
    for tid, p in sorted(wb.ciq_pilot.items()):
        stock = str(p["Stock"])
        entry, exit_ = p["Entry"].date(), p["Exit"].date()
        re_, rx = by_day[entry], by_day[exit_]
        s0, s1 = _ciq_level(re_, _CIQ_COL[stock]), _ciq_level(rx, _CIQ_COL[stock])
        w0, w1 = _ciq_level(re_, "msci_world_net"), _ciq_level(rx, "msci_world_net")
        assert s0 and s1 and w0 and w1
        rs, rw = s1 / s0 - 1.0, w1 / w0 - 1.0
        out.append({
            "test_id": tid, "src": p["_src"], "entry": entry, "exit": exit_,
            "ciq_rows": f"CIQ Daily Data rows {re_.row} / {rx.row}",
            "stored_stock_tr": p["Stock TR"], "recomputed_stock_tr": rs,
            "stored_world": p["MSCI World Net TR"], "recomputed_world": rw,
            "stored_excess": p["Excess vs World"], "recomputed_excess": rs - rw,
            "max_abs_diff": max(abs(rs - p["Stock TR"]), abs(rw - p["MSCI World Net TR"])),
        })
    return out


def pilot_vs_polygon(wb: AuditWorkbook, ledger: list[Obs]) -> list[dict[str, Any]]:
    """Two questions, kept apart. (a) REPRODUCTION: same sessions, same CIQ benchmark series, only
    the stock source differs — does Polygon give CIQ's number? (b) CURRENCY: the CIQ 'MSCI World'
    series is not USD (``benchmarks.currency_fit``); what is the excess against a USD benchmark?"""
    by_id = {o.test_id: o for o in ledger if o.test_id}
    out: list[dict[str, Any]] = []
    for tid, p in sorted(wb.ciq_pilot.items()):
        o = by_id.get(tid)
        row: dict[str, Any] = {
            "test_id": tid, "ciq_entry": p["Entry"].date(), "ciq_exit": p["Exit"].date(),
            "ciq_stock_tr": p["Stock TR"], "ciq_world": p["MSCI World Net TR"],
            "ciq_excess": p["Excess vs World"], "ciq_outcome": p["Outcome vs World"],
        }
        if o is None or o.stock_return is None or o.excess_vs_ciq_msci_series is None:
            row.update(polygon_status=o.status if o else "MISSING", verdict="NOT REPRODUCED")
            out.append(row)
            continue
        d_stock = (o.stock_return - p["Stock TR"]) * 100
        d_excess = (o.excess_vs_ciq_msci_series - p["Excess vs World"]) * 100
        same_dates = (o.entry_date == row["ciq_entry"].isoformat()
                      and o.exit_date == row["ciq_exit"].isoformat())
        same_bench_outcome = ("OUTPERFORMED" if o.excess_vs_ciq_msci_series > 0
                              else "UNDERPERFORMED")
        usd_outcome = ("" if o.excess_vs_world is None else
                       "OUTPERFORMED" if o.excess_vs_world > 0 else "UNDERPERFORMED")
        row.update(
            polygon_entry=o.entry_date, polygon_exit=o.exit_date, same_sessions=same_dates,
            polygon_stock_tr=o.stock_return, polygon_price_only=o.price_return,
            polygon_ciq_series=o.ciq_msci_series_return,
            polygon_excess_same_benchmark=o.excess_vs_ciq_msci_series,
            diff_stock_pp=d_stock, diff_excess_pp=d_excess,
            sign_agrees=(same_bench_outcome == p["Outcome vs World"]),
            verdict=("MATERIAL — investigate" if abs(d_stock) > MATERIAL_PP or not same_dates
                     else "REPRODUCED WITHIN TOLERANCE"),
            usd_benchmark=o.world_benchmark, usd_benchmark_return=o.world_return,
            usd_excess=o.excess_vs_world, usd_outcome=usd_outcome,
            currency_effect_pp=(None if o.excess_vs_world is None
                                else (o.excess_vs_world - p["Excess vs World"]) * 100),
            usd_outcome_differs_from_pilot=(usd_outcome != p["Outcome vs World"]),
        )
        out.append(row)
    return out


def path_diagnostics(wb: AuditWorkbook, series: dict[str, Series],
                     ticker: str) -> dict[str, Any]:
    """CIQ's cumulative path vs Polygon TR and price-only paths, rebased on CIQ's base date."""
    attr = _CIQ_COL[ticker]
    ciq = {r.day: v for r in wb.ciq_daily if (v := _ciq_level(r, attr)) is not None}
    s = series[ticker]
    common = sorted(d for d in ciq if d in s.by_day)
    base = common[0]
    b_tr, b_px, b_ciq = s.by_day[base].adj_close, s.by_day[base].close, ciq[base]

    def path(d: date) -> tuple[float, float, float]:
        q = s.by_day[d]
        return ciq[d] / b_ciq, q.adj_close / b_tr, q.close / b_px

    diff_tr = [abs(path(d)[0] - path(d)[1]) for d in common]
    diff_px = [abs(path(d)[0] - path(d)[2]) for d in common]
    daily: list[float] = []
    for d0, d1 in zip(common, common[1:], strict=False):
        c = ciq[d1] / ciq[d0] - 1
        t = s.by_day[d1].adj_close / s.by_day[d0].adj_close - 1
        daily.append((c - t) * 100)
    ex_rows: list[dict[str, Any]] = []
    for dv in s.dividends_used:
        if dv.ex_date not in ciq or dv.ex_date not in s.by_day:
            continue
        i = common.index(dv.ex_date)
        if i == 0:
            continue
        d0 = common[i - 1]
        q0, q1 = s.by_day[d0], s.by_day[dv.ex_date]
        ex_rows.append({
            "ticker": ticker, "ex_date": dv.ex_date, "cash": dv.cash,
            "ciq_1d": ciq[dv.ex_date] / ciq[d0] - 1,
            "polygon_tr_1d": q1.adj_close / q0.adj_close - 1,
            "polygon_price_1d": q1.close / q0.close - 1,
            "dividend_yield_1d": dv.cash / q0.close,
        })
    closer = "dividends-reinvested (TR)" if sum(diff_tr) < sum(diff_px) else "price-only"
    end = common[-1]
    return {
        "ticker": ticker, "ciq_column": attr, "base": base, "last_common": end,
        "n_common": len(common),
        "end_ciq": path(end)[0], "end_polygon_tr": path(end)[1], "end_polygon_price": path(end)[2],
        "max_abs_gap_vs_tr": max(diff_tr), "max_abs_gap_vs_price": max(diff_px),
        "mean_abs_gap_vs_tr": statistics.fmean(diff_tr),
        "mean_abs_gap_vs_price": statistics.fmean(diff_px),
        "daily_ret_diff_pp_mean": statistics.fmean(daily),
        "daily_ret_diff_pp_sd": statistics.pstdev(daily),
        "daily_ret_diff_pp_maxabs": max(abs(x) for x in daily),
        "ciq_closer_to": closer, "ex_dates": ex_rows,
        # full lists, never sliced — a reader is told the whole population
        "weekdays_in_ciq_not_polygon": [d.isoformat() for d in sorted(ciq)
                                        if d not in s.by_day and base <= d <= end
                                        and d.weekday() < 5],
        "polygon_days_not_in_ciq": [d.isoformat() for d in sorted(s.by_day)
                                    if d not in ciq and base <= d <= end],
        "log_gap_end": math.log(path(end)[0] / path(end)[1]),
    }
