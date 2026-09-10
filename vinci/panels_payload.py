"""(phase 6) STRUCTURED payloads for the panel grid — values, never markup.

WHY THIS FILE NO LONGER RENDERS. Its first cut emitted HTML, which put a SECOND renderer
beside the frontend's JS views: the same design drawn twice, in two languages, guaranteed to
drift. The frontend is a JS SPA reading committed JSON (`frontend/build.py` may not even import
`vinci`), so the division is settled — **this module produces structured values and nothing
else; `frontend/views/shared/panels.js` is the only renderer.** The approved preview design now
lives there.

Every value here is read from a STRUCTURED field on a committed artifact — `own_history`'s
numeric series, a row's float returns, the instruments list — never re-parsed out of a rendered
line. That is the house rule, and the reason is on record: a thousands-blind re-parse of a
`$1,101.80M` display string read it as `1`.

PAYLOAD SHAPES, by panel key. Each is a plain JSON object; the renderer formats it and must tolerate
a missing optional key (an older committed snapshot will not carry a field added later):

  the_call            {verdict, sleeve, entry_date, entry_price, current_price, closed,
                       horizon_date, benchmark}
  kills               {criteria: [{text, metric, reading, threshold, unit_checked}]}
  multiple_and_price  {metric, current, low, high, median, percentile, n_closes, as_of,
                       series: [[date, value], …], current_is_last_point,
                       range_excludes_current}
  filing_watch        {last_evidence_date, last_evidence_source, newer_filings: [...],
                       next_expected_print, next_expected_basis, unread_print}
  dilution            {line, forms: [[form, count], …], window_days}
  attribution         {position_return, benchmark, benchmark_return, excess, days_elapsed,
                       horizon_days}
  sources             {refs: [...]}
  commissioning       {periods: [{period, not_yet_in_service, in_service, ratio, like_for_like}]}
  segment_economics   {rows: [{segment, metric, period, value}]}
  cost_of_borrowing   {fixed_pct, fixed_coverage, all_in_pct, all_in_coverage, floating_share,
                       lease_musd, total_musd, n_covered, n_total}
"""
from __future__ import annotations

from typing import Any

from vinci.borrowing import BorrowingUnavailableError, borrowing


def _num(x: Any) -> float | None:
    """A committed numeric field → float, or None. Never a coerced zero."""
    if isinstance(x, bool) or x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    return None


def the_call(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "verdict": row.get("verdict"), "sleeve": row.get("sleeve"),
        "entry_date": row.get("entry_date"), "entry_price": _num(row.get("entry_price")),
        "current_price": _num(row.get("current_price")), "closed": bool(row.get("closed")),
        "horizon_date": row.get("horizon_date"), "benchmark": row.get("benchmark"),
    }


def attribution(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "position_return": _num(row.get("position_return")),
        "benchmark": row.get("benchmark"),
        "benchmark_return": _num(row.get("benchmark_return")),
        "excess": _num(row.get("excess")),
        "days_elapsed": row.get("days_elapsed"), "horizon_days": row.get("horizon_days"),
    }


def multiple_and_price(valuation: dict[str, Any]) -> dict[str, Any] | None:
    """The name's own multiple history. SERIES PASSES THROUGH AS NUMBERS — the renderer draws the
    sparkline from these pairs, so no chart geometry is computed here and none is parsed there."""
    hist = (valuation.get("own_history") or {}).get("value") or []
    if not hist or not isinstance(hist, list):
        return None
    h = hist[0]
    cur = _num(h.get("current"))
    if cur is None:
        return None
    series: list[list[Any]] = [[str(d), float(v)] for d, v in (h.get("series") or [])
                               if _num(v) is not None]
    # THE SERIES IS ONE POINT LONGER THAN THE RANGE WINDOW, on 16 of the 18 corpus names, and the
    # extra point is the CURRENT mark appended to the historical closes. `low`/`high`/`median`/
    # `percentile` are struck over the HISTORICAL window and exclude it — which is why SMPL's
    # current 5.56x sits BELOW its own stated 6.11x low, a real state and not a data error.
    #
    # Stated as a FLAG rather than left to the renderer to infer: a sparkline drawn over every point
    # beneath a band drawn over n_closes would show a line leaving its own range with nothing saying
    # why, and the obvious "fix" for that appearance is to widen the band — which would silently
    # restate the percentile the whole panel turns on.
    n = h.get("n_closes")
    current_is_last = (
        isinstance(n, int) and len(series) == n + 1
        and bool(series) and abs(float(series[-1][1]) - cur) < 1e-9
    )
    return {
        "metric": h.get("metric"), "current": cur,
        "low": _num(h.get("low")), "high": _num(h.get("high")),
        "median": _num(h.get("median")), "percentile": _num(h.get("percentile")),
        "n_closes": n, "as_of": h.get("as_of"), "series": series,
        "current_is_last_point": current_is_last,
        "range_excludes_current": current_is_last,
    }


def filing_watch(freshness: dict[str, Any]) -> dict[str, Any]:
    return {
        "last_evidence_date": freshness.get("last_evidence_date"),
        "last_evidence_source": freshness.get("last_evidence_source"),
        "newer_filings": list(freshness.get("newer_filings") or []),
        "next_expected_print": freshness.get("next_expected_print"),
        "next_expected_basis": freshness.get("next_expected_basis"),
        "unread_print": bool(freshness.get("unread_print")),
    }


def kills(freshness: dict[str, Any], record: dict[str, Any] | None) -> dict[str, Any]:
    """The criteria, with a measured reading beside any that has one.

    THE MACHINE SURFACES, THE HUMAN CONCLUDES — `vinci/monitor.py` refuses to adjudicate a trigger
    as fired and nothing here weakens that. A reading is printed BESIDE its criterion; no field says
    "fired", and the renderer has no state that could.

    `unit_checked` is carried because 0 of 479 resolvable paths in the corpus carry a unit, so the
    evaluator's unit check has never fired — a `$551.974M` reading against a `$bn` threshold would
    read as crossed. The flag travels with the reading so the surface can mark it.
    """
    measured = ((record or {}).get("verdict") or {}).get("measured_triggers") or []
    by_text = {str(m.get("criterion") or m.get("text") or ""): m for m in measured
               if isinstance(m, dict)}
    out = []
    for text in (freshness.get("triggers") or []):
        m = by_text.get(str(text)) or {}
        out.append({
            "text": text,
            "metric": m.get("metric"), "reading": _num(m.get("reading")),
            "threshold": _num(m.get("threshold")),
            "unit_checked": bool(m.get("unit_checked")),
        })
    return {"criteria": out}


def dilution(pipeline: dict[str, Any]) -> dict[str, Any]:
    forms: dict[str, int] = {}
    for f in pipeline.get("filings") or []:
        if isinstance(f, dict):
            k = str(f.get("form"))
            forms[k] = forms.get(k, 0) + 1
    return {
        "line": (pipeline.get("line") or {}).get("value"),
        "forms": sorted(forms.items(), key=lambda kv: (-kv[1], kv[0])),
        "window_days": pipeline.get("window_days"),
    }


def sources(primary: dict[str, Any]) -> dict[str, Any]:
    refs: list[str] = []
    filing = primary.get("filing") or {}
    if filing.get("source_ref"):
        refs.append(str(filing["source_ref"]))
    for r in primary.get("releases") or []:
        if isinstance(r, dict) and r.get("source_ref"):
            refs.append(str(r["source_ref"]))
    return {"refs": refs}


def cost_of_borrowing(capital_structure: dict[str, Any]) -> dict[str, Any] | None:
    """None when the stack cannot be priced — the caller turns that into the panel's refusal.

    COVERAGE TRAVELS WITH THE RATE, always. AORT's fixed average is struck over one $0.9M bond in a
    $220.9M stack; a renderer that shows 6.05% without 0.4% beside it repeats the lease defect one
    level down, so the payload cannot express a rate without its coverage.
    """
    ins = capital_structure.get("instruments") or {}
    try:
        b = borrowing(ins.get("value"), source_ref=str(ins.get("source_ref") or ""))
    except BorrowingUnavailableError:
        return None
    return {
        "fixed_pct": b.weighted_avg_coupon_pct, "fixed_coverage": b.coverage,
        "all_in_pct": b.all_in_rate_pct, "all_in_coverage": b.all_in_coverage,
        "floating_share": b.floating_share, "lease_musd": b.lease_musd,
        "total_musd": b.total_musd, "n_covered": b.n_covered, "n_total": b.n_total,
    }
