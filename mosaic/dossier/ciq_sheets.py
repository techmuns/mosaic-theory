"""Sheet-semantics extractors — turn CIQ workbook subsheets into source-bound dossier facts.

Each extractor resolves an explicit (workbook, sheet) ADDRESS via :meth:`CiqBundle.sheet` and the
reading rules bound to that sheet (per ``ciq_extraction_notes.md``): Multiples uses the Close
column and EXCLUDES the partial-period last column from the historical distribution (using it as the
current value); growth respects the Reclassified-basis boundary; empty/'-'/'NM'/'Entitlement Needed'
are UNAVAILABLE, never 0. Fail loud — a missing WORKBOOK → MISSING ("pull CIQ"); a present workbook
with an absent/garbled sheet → UNKNOWN with the reason — never a fabricated number.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from mosaic.dossier.ciq import (
    _UNAVAILABLE_CELLS,
    CiqBundle,
    CiqParseError,
    CiqUnavailableError,
    clean_num,
    excel_date,
    read_text,
)
from mosaic.dossier.schemas import Sourced

Rows = list[list[Any]]

_MULT_HEADER = ("For Quarter Ending", "For Period Ending", "For the Period")
_RANGE_BANDS = (
    (0.25, "near-floor"), (0.50, "below-center"), (0.75, "above-center"), (1.01, "near-ceiling"),
)


# --- shared helpers ---------------------------------------------------------------------------


def _miss_or_unknown(bundle: CiqBundle, kind: str, exc: Exception) -> Sourced[Any]:
    """Missing WORKBOOK → MISSING; present workbook + bad sheet → UNKNOWN. Never faked."""
    if not bundle.has(kind):
        return Sourced.missing(note=f"CIQ '{kind}' export not found for {bundle.ticker} — pull it")
    return Sourced.unknown(note=str(exc))


def _find_row(rows: Rows, label: str) -> int | None:
    return next((i for i, r in enumerate(rows) if r and str(r[0]).strip() == label), None)


def _period_header(rows: Rows) -> int | None:
    return next((i for i, r in enumerate(rows) if r and "Fiscal Period" in str(r[0])), None)


def _reclassified_cols(header: list[Any]) -> set[int]:
    return {j for j, c in enumerate(header) if isinstance(c, str) and "Reclassified" in c}


def _is_ltm(cell: Any) -> bool:
    """A period-header cell whose label marks a trailing-twelve-month column (vs a fiscal year)."""
    return "LTM" in str(cell).upper()


def _find_row_prefix(rows: Rows, label: str) -> int | None:
    return next((i for i, r in enumerate(rows) if r and str(r[0]).strip().startswith(label)), None)


def _usd(v: float | None) -> str:  # a dollar figure → "$9.71", or em-dash when absent
    return f"${v:,.2f}" if v is not None else "—"


def _pct1(v: float | None) -> str:  # a fraction → "1.9%" (one decimal), or em-dash when absent
    return f"{v * 100:.1f}%" if v is not None else "—"


def _latest_col(rows: Rows, ri: int, hdr: int | None) -> tuple[int, float, str] | None:
    """The rightmost column of row ``ri`` carrying a value → (col, value, period-label)."""
    valid = [(j, clean_num(rows[ri][j])) for j in range(1, len(rows[ri]))]
    present = [(j, v) for j, v in valid if v is not None]
    if not present:
        return None
    j, v = present[-1]
    period = ""
    if hdr is not None and j < len(rows[hdr]):
        period = str(rows[hdr][j]).strip().replace("\n", " ")
    return j, v, period


def _multiples_close(rows: Rows, metric: str) -> list[tuple[Any, float | None]]:
    """(date, Close) pairs for a metric block across the dated columns. Close — not Average/High/Low
    (notes line 197); date from the serial header (line 126); empty/NM → None."""
    hdr = next(
        (
            i for i, r in enumerate(rows)
            if r and any(str(r[0]).strip().startswith(h) for h in _MULT_HEADER)
        ),
        None,
    )
    lbl = _find_row(rows, metric)
    if hdr is None or lbl is None:
        return []
    close = next(
        (
            i for i in range(lbl, min(lbl + 6, len(rows)))
            if len(rows[i]) > 1 and str(rows[i][1]).strip() == "Close"
        ),
        None,
    )
    if close is None:
        return []
    cols = range(2, min(len(rows[hdr]), len(rows[close])))
    return [(excel_date(rows[hdr][j]), clean_num(rows[close][j])) for j in cols]


# --- valuation: Multiples (Financials → Multiples, historical) --------------------------------


def ev_ebitda_percentile(bundle: CiqBundle) -> Sourced[float]:
    """Percentile of the current TEV/LTM EBITDA Close within its own quarterly history (0=floor)."""
    try:
        rows = bundle.sheet("financials", "Multiples", freq="quarterly")
    except CiqUnavailableError as exc:
        return _miss_or_unknown(bundle, "financials", exc)
    series = [v for _, v in _multiples_close(rows, "TEV/LTM EBITDA") if v is not None]
    if len(series) < 4:
        return Sourced.unknown(note=f"TEV/LTM EBITDA Close <4 quarters ({len(series)}) — no pctile")
    current, history = series[-1], series[:-1]  # partial last col = current, excluded from history
    pct = sum(1 for h in history if h <= current) / len(history)
    return Sourced.present(
        round(pct, 3),
        source_ref=f"CIQ Financials→Multiples 'TEV/LTM EBITDA' Close — {len(history)} quarters "
        "(partial last column excluded from the distribution)",
    )


def range_position(bundle: CiqBundle) -> Sourced[str]:
    """Headline current multiples + EV/EBITDA range position (near-floor … near-ceiling)."""
    try:
        rows = bundle.sheet("financials", "Multiples", freq="quarterly")
    except CiqUnavailableError as exc:
        return _miss_or_unknown(bundle, "financials", exc)
    ev = [v for _, v in _multiples_close(rows, "TEV/LTM EBITDA") if v is not None]
    pe = [v for _, v in _multiples_close(rows, "P/LTM EPS") if v is not None]
    if len(ev) < 4:
        return Sourced.unknown(note="TEV/LTM EBITDA Close has <4 quarters — no range position")
    cur, hist = ev[-1], ev[:-1]
    pct = sum(1 for h in hist if h <= cur) / len(hist)
    band = next(b for t, b in _RANGE_BANDS if pct <= t)
    tail = f"; P/LTM EPS {pe[-1]:.1f}x" if pe else ""
    return Sourced.present(
        f"EV/EBITDA (TEV/LTM) {cur:.1f}x at {pct:.0%}ile of {len(hist)} closes → {band}{tail}",
        source_ref="CIQ Financials→Multiples (Close; last col = current, excluded from history)",
    )


def ev_ebitda_current(bundle: CiqBundle) -> Sourced[float]:
    """The current TEV/LTM EBITDA — the authoritative EV/EBITDA, a MULTIPLE (~8.5x) not a dollar
    figure. Latest Close of the trailing block. Fail loud when the Multiples sheet is absent."""
    try:
        rows = bundle.sheet("financials", "Multiples", freq="quarterly")
    except CiqUnavailableError as exc:
        return _miss_or_unknown(bundle, "financials", exc)
    ev = [v for _, v in _multiples_close(rows, "TEV/LTM EBITDA") if v is not None]
    if not ev:
        return Sourced.unknown(note="TEV/LTM EBITDA Close has no value")
    return Sourced.present(
        round(ev[-1], 1),
        source_ref="CIQ Financials→Multiples 'TEV/LTM EBITDA' Close (latest) — current multiple",
    )


def pe_ltm_current(bundle: CiqBundle) -> Sourced[float]:
    """Current P/LTM EPS (latest Close) — GAAP-trailing, for cross-checking the EDGAR P/E basis."""
    try:
        rows = bundle.sheet("financials", "Multiples", freq="quarterly")
    except CiqUnavailableError as exc:
        return _miss_or_unknown(bundle, "financials", exc)
    pe = [v for _, v in _multiples_close(rows, "P/LTM EPS") if v is not None]
    if not pe:
        return Sourced.unknown(note="P/LTM EPS Close has no value")
    return Sourced.present(
        round(pe[-1], 1), source_ref="CIQ Financials→Multiples 'P/LTM EPS' Close (latest)"
    )


# --- quality: Cash Flow / Income Statement / Capital Structure Details ------------------------


def free_cash_flow(bundle: CiqBundle) -> Sourced[float]:
    try:
        rows = bundle.sheet("financials", "Cash Flow", freq="annual")
    except CiqUnavailableError as exc:
        return _miss_or_unknown(bundle, "financials", exc)
    ri = _find_row(rows, "Levered Free Cash Flow")
    if ri is None:
        return Sourced.unknown(note="Cash Flow sheet has no 'Levered Free Cash Flow' row")
    latest = _latest_col(rows, ri, _period_header(rows))
    if latest is None:
        return Sourced.unknown(note="Levered Free Cash Flow has no value in any period")
    _, value, period = latest
    return Sourced.present(
        round(value, 1), source_ref=f"CIQ Financials→Cash Flow 'Levered Free Cash Flow' [{period}]"
    )


def interest_coverage(bundle: CiqBundle) -> Sourced[float]:
    try:
        rows = bundle.sheet("financials", "Income Statement", freq="annual")
    except CiqUnavailableError as exc:
        return _miss_or_unknown(bundle, "financials", exc)
    e_i, i_i = _find_row(rows, "EBITDA"), _find_row(rows, "Interest Expense")
    hdr = _period_header(rows)
    if e_i is None or i_i is None:
        return Sourced.unknown(note="Income Statement missing EBITDA or Interest Expense row")
    col = next(
        (
            j
            for j in range(len(rows[e_i]) - 1, 0, -1)
            if clean_num(rows[e_i][j]) is not None
            and j < len(rows[i_i])
            and clean_num(rows[i_i][j]) is not None
        ),
        None,
    )
    if col is None:
        return Sourced.unknown(note="no period with both EBITDA and Interest Expense")
    ebitda, interest = clean_num(rows[e_i][col]), clean_num(rows[i_i][col])
    if not interest or ebitda is None:
        return Sourced.unknown(note="interest expense is zero/unavailable")
    period = str(rows[hdr][col]).strip().replace("\n", " ") if hdr is not None else ""
    return Sourced.present(
        round(ebitda / abs(interest), 1),
        source_ref=f"CIQ Financials→Income Statement EBITDA ÷ Interest Expense [{period}]",
    )


def _quarter_token(cell: Any) -> str | None:
    m = re.search(r"\bQ([1-4])\b", str(cell))
    return f"Q{m.group(1)}" if m else None


def _short_period(cell: Any) -> str:
    s = str(cell).replace("\n", " ").strip()
    m = re.search(r"(Q[1-4]).*?([A-Z][a-z]{2}-[\d-]*\d{4})", s)
    return f"{m.group(1)} {m.group(2)}" if m else s[:16]


def _quarterly_revenue_yoy(bundle: CiqBundle) -> str | None:
    """Clean same-basis revenue YoY from the QUARTERLY Income Statement: the latest quarter vs the
    same quarter a year earlier (Q1 vs the prior Q1), same period-type AND reclassified basis (notes
    ~line 204). None when no same-quarter, same-basis prior exists — caller falls to UNAVAILABLE."""
    try:
        rows = bundle.sheet("financials", "Income Statement", freq="quarterly")
    except CiqUnavailableError:
        return None
    hdr, rev_i = _period_header(rows), _find_row(rows, "Total Revenue")
    if hdr is None or rev_i is None:
        return None
    latest = _latest_col(rows, rev_i, hdr)
    if latest is None:
        return None
    col, rev, _ = latest
    q = _quarter_token(rows[hdr][col]) if col < len(rows[hdr]) else None
    if q is None:
        return None
    recl = _reclassified_cols(rows[hdr])
    base = col in recl
    for j in range(col - 1, 0, -1):  # nearest earlier same-quarter column on the same basis
        if j < len(rows[hdr]) and _quarter_token(rows[hdr][j]) == q and (j in recl) == base:
            pv = clean_num(rows[rev_i][j])
            if not pv:
                return None
            cur, pri = _short_period(rows[hdr][col]), _short_period(rows[hdr][j])
            return f"{rev / pv - 1:+.1%} ({cur} vs {pri})"
    return None


def margin_trend(bundle: CiqBundle) -> Sourced[str]:
    """The MARGIN trajectory — gross and EBITDA margin (%) per period across the years, so the trend
    is visible (e.g. VRRM's ~42%→37% EBITDA-margin compression). Each margin is a ratio within one
    column, so the Reclassified basis (marked) is never crossed. Revenue GROWTH is a top-line metric
    and lives in the multi-year trajectory, not under a margin label."""
    try:
        rows = bundle.sheet("financials", "Income Statement", freq="annual")
    except CiqUnavailableError as exc:
        return _miss_or_unknown(bundle, "financials", exc)
    hdr, rev_i = _period_header(rows), _find_row(rows, "Total Revenue")
    if rev_i is None or hdr is None:
        return Sourced.unknown(note="Income Statement missing Total Revenue / period header")

    def margin_traj(ri: int | None) -> str | None:
        if ri is None:
            return None
        parts: list[str] = []
        for j in range(1, len(rows[ri])):
            v = clean_num(rows[ri][j])
            rv = clean_num(rows[rev_i][j]) if j < len(rows[rev_i]) else None
            if v is not None and rv:
                lab = _period_label(rows[hdr][j]) if j < len(rows[hdr]) else f"c{j}"
                parts.append(f"{lab} {v / rv:.0%}")
        return " → ".join(parts) if len(parts) >= 2 else None

    eb_traj = margin_traj(_find_row(rows, "EBITDA"))
    gp_traj = margin_traj(_find_row(rows, "Gross Profit"))
    if eb_traj is None and gp_traj is None:
        return Sourced.unknown(note="no gross/EBITDA margin series in the Income Statement")
    bits = [f"EBITDA margin: {eb_traj}"] if eb_traj else []
    if gp_traj:
        bits.append(f"gross margin: {gp_traj}")
    return Sourced.present(
        "; ".join(bits) + "  [R reclassified basis; each margin is within one period]",
        source_ref="CIQ Financials→Income Statement (margin trajectory)",
    )


def liquidity_covenant_flags(bundle: CiqBundle) -> Sourced[str]:
    try:
        rows = bundle.sheet("financials", "Capital Structure Details", freq="annual")
    except CiqUnavailableError as exc:
        return _miss_or_unknown(bundle, "financials", exc)
    hdr = _find_row(rows, "Description")  # the latest FY section's instrument table
    if hdr is None:
        return Sourced.unknown(note="Capital Structure Details has no instrument table")
    insts: list[str] = []
    for i in range(hdr + 1, min(hdr + 12, len(rows))):
        desc = str(rows[i][0]).strip()
        if not desc or desc.startswith("FY ") or desc == "Description":
            break
        typ = str(rows[i][1]).strip() if len(rows[i]) > 1 else ""
        principal = clean_num(rows[i][2]) if len(rows[i]) > 2 else None
        coupon = str(rows[i][3]).strip() if len(rows[i]) > 3 else ""
        amt = f"{principal:,.0f}" if principal is not None else "undrawn/–"
        insts.append(f"{desc} ({typ}) {amt} @ {coupon}")
    if not insts:
        return Sourced.unknown(note="no debt instruments parsed")
    return Sourced.present("; ".join(insts), source_ref="CIQ Financials→Capital Structure Details")


# --- concentration: Segments ------------------------------------------------------------------


def _segment_section(
    bundle: CiqBundle, section: str, *, after_label: str | None = None, total_label: str = "Total",
    extra_fn: Callable[[float, str], str] | None = None, source_note: str = "",
) -> Sourced[str]:
    """Revenue/EBITDA share for a Segments-sheet section. ``after_label`` scopes the search past a
    sub-header (e.g. 'Geographic Segments') so the SAME 'Revenues' block under it is found, not
    the first one — same parsing for business segments and geography."""
    try:
        rows = bundle.sheet("financials", "Segments", freq="annual")
    except CiqUnavailableError as exc:
        return _miss_or_unknown(bundle, "financials", exc)
    hdr = _period_header(rows)
    floor = 0
    if after_label is not None:
        a = next((i for i, r in enumerate(rows) if r and after_label in str(r[0])), None)
        if a is None:
            return Sourced.unknown(note=f"Segments sheet has no '{after_label}' section")
        floor, hdr = a, _period_header(rows[a:])
        hdr = hdr + a if hdr is not None else None
    start = next(
        (i for i in range(floor, len(rows)) if rows[i] and str(rows[i][0]).strip() == section), None
    )
    total = next(
        (
            i for i in range(floor, len(rows))
            if rows[i] and str(rows[i][0]).strip().startswith(f"Total {section.rstrip('s')}")
        ),
        None,
    )
    if start is None or total is None or hdr is None:
        return Sourced.unknown(note=f"Segments sheet has no '{section}' section as expected")
    latest = _latest_col(rows, total, hdr)
    if latest is None:
        return Sourced.unknown(note=f"Segments 'Total {section}' has no value")
    col, tot, period = latest
    parts: list[str] = []
    for i in range(start + 1, total):
        seg = str(rows[i][0]).strip()
        v = clean_num(rows[i][col]) if col < len(rows[i]) else None
        if seg and v is not None and tot:
            parts.append(f"{seg} {v:,.0f} ({v / tot:.0%})")
    if not parts:
        return Sourced.unknown(note=f"no {section} segment rows with values")
    label = f"{after_label} → {section}" if after_label else section
    tail = extra_fn(tot, period) if extra_fn else ""
    return Sourced.present(
        f"[{period}] " + "; ".join(parts) + f" of {total_label} {tot:,.0f}{tail}",
        source_ref=f"CIQ Financials→Segments ({label}, latest annual column){source_note}",
    )


def _consolidated_ebitda(bundle: CiqBundle, period: str) -> float | None:
    """Consolidated EBITDA (Income Statement) for the FY period matching a segment column — the
    behind the multiples/leverage/coverage, vs the pre-corporate segment sum."""
    m = re.search(r"[A-Z][a-z]{2}-[\d-]*\d{4}", period)
    if m is None:
        return None
    token = m.group(0)
    try:
        rows = bundle.sheet("financials", "Income Statement", freq="annual")
    except CiqUnavailableError:
        return None
    hdr, eb_i = _period_header(rows), _find_row(rows, "EBITDA")
    if hdr is None or eb_i is None:
        return None
    col = next(
        (
            j for j in range(1, len(rows[hdr]))
            if token in str(rows[hdr][j]) and "LTM" not in str(rows[hdr][j]).upper()
        ),
        None,
    )
    return clean_num(rows[eb_i][col]) if col is not None and col < len(rows[eb_i]) else None


def segments(bundle: CiqBundle) -> Sourced[str]:
    """Segment REVENUE mix + each segment's share of total revenue."""
    return _segment_section(bundle, "Revenues")


def segment_ebitda(bundle: CiqBundle) -> Sourced[str]:
    """Segment EBITDA mix — each share is of the SEGMENT-EBITDA sum (pre-corporate), explicitly
    distinguished from the CONSOLIDATED EBITDA behind the multiples/leverage; the reconciling
    unallocated-corporate item is surfaced so the two 'EBITDA' bases aren't confused."""

    def reconcile(tot: float, period: str) -> str:
        cons = _consolidated_ebitda(bundle, period)
        if cons is None:
            return ""
        return f"; consolidated EBITDA {cons:,.0f} (~{tot - cons:,.0f} unallocated corporate)"

    return _segment_section(
        bundle, "EBITDA", total_label="segment-EBITDA sum (pre-corporate)", extra_fn=reconcile,
        source_note=" + Income Statement (consolidated EBITDA)",
    )


def geographic(bundle: CiqBundle) -> Sourced[str]:
    """Revenue by geography — the Segments sheet's 'Geographic Segments' → 'Revenues' block, parsed
    like the business-segment revenue share. Fail loud UNKNOWN only if the section is absent."""
    return _segment_section(bundle, "Revenues", after_label="Geographic Segment")


def _period_label(cell: Any) -> str:
    """A compact period label + basis markers — 'Dec-2024 (R)' reclassified, 'Mar-31-2026 (LTM)'."""
    s = str(cell).replace("\n", " ").strip()
    m = re.search(r"([A-Z][a-z]{2}-[\d-]*\d{4}|\d{4})", s)
    suffix = (" (R)" if "Reclassified" in s else "") + (" (LTM)" if "LTM" in s.upper() else "")
    return (m.group(1) if m else s[:10]) + suffix


def _fmt_num(v: float) -> str:
    return f"{v:,.0f}"


def _fmt_pct(v: float) -> str:
    return f"{v * 100:.1f}%"


def _trajectory_row(
    rows: Rows, ri: int | None, hdr: int | None, fmt: Callable[[float], str] = _fmt_num
) -> str | None:
    """The multi-period series for a row: 'period value' per column, basis marked — NEVER YoY'd
    across (the human sees growth-vs-decline; cross-basis growth is not computed)."""
    if ri is None or hdr is None:
        return None
    parts = [
        f"{_period_label(rows[hdr][j]) if j < len(rows[hdr]) else f'c{j}'} {fmt(v)}"
        for j in range(1, len(rows[ri]))
        if (v := clean_num(rows[ri][j])) is not None
    ]
    return " → ".join(parts) if len(parts) >= 2 else None


def multi_year_trajectory(bundle: CiqBundle) -> Sourced[str]:
    """The multi-year arc (values per period, basis noted, never YoY'd across the Reclassified
    boundary) for total revenue, EBITDA, and segment EBITDA — the compounder-vs-melting-ice signal:
    was the business growing or declining pre-catalyst?"""
    lines: list[str] = []
    try:
        inc = bundle.sheet("financials", "Income Statement", freq="annual")
        ihdr = _period_header(inc)
        if (rev := _trajectory_row(inc, _find_row(inc, "Total Revenue"), ihdr)) is not None:
            lines.append(f"Revenue: {rev}")
        if (eb := _trajectory_row(inc, _find_row(inc, "EBITDA"), ihdr)) is not None:
            lines.append(f"EBITDA: {eb}")
    except CiqUnavailableError:
        pass
    if (yoy := _quarterly_revenue_yoy(bundle)) is not None:  # latest top-line growth (moved here)
        lines.append(f"Revenue YoY (latest same-quarter): {yoy}")
    try:
        seg = bundle.sheet("financials", "Segments", freq="annual")
        shdr = _period_header(seg)
        eb_start = _find_row(seg, "EBITDA")
        for i in range(eb_start + 1, min(eb_start + 6, len(seg))) if eb_start is not None else []:
            name = str(seg[i][0]).strip()
            if not name or name.startswith("Total"):
                break
            if (arc := _trajectory_row(seg, i, shdr)) is not None:
                lines.append(f"{name} EBITDA: {arc}")
    except CiqUnavailableError:
        pass
    try:  # ROIC arc (item 5) — returns quality over time, alongside the revenue/EBITDA arc
        rat = bundle.sheet("financials", "Ratios", freq="annual")
        roic = _trajectory_row(
            rat, _find_row(rat, "Return on Capital %"), _period_header(rat), _fmt_pct
        )
        if roic is not None:
            lines.append(f"ROIC: {roic}")
    except CiqUnavailableError:
        pass
    if not lines:
        return Sourced.unknown(note="no multi-year revenue/EBITDA series in the sheets")
    return Sourced.present(
        "; ".join(lines) + "  [R reclassified; per-period values, never YoY'd across a basis]",
        source_ref="CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)",
    )


def surprise_history(bundle: CiqBundle) -> Sourced[str]:
    """Estimate beat/miss history from Estimates→Surprise — the pre-catalyst 'cracks' (EPS & revenue
    actual-vs-consensus). The sheet is by FISCAL YEAR (no quarterly view) — annual surprise;
    +beat / −miss. Fail loud if the sheet/rows are absent."""
    try:
        rows = bundle.sheet("estimates", "Surprise")
    except CiqUnavailableError as exc:
        return _miss_or_unknown(bundle, "estimates", exc)
    yhdr = next(
        (
            i for i, r in enumerate(rows)
            if sum(1 for c in r[1:10] if (n := clean_num(c)) is not None and 2000 < n < 2100) >= 3
        ),
        None,
    )
    if yhdr is None:
        return Sourced.unknown(note="Surprise sheet has no fiscal-year header row")

    def series(ri: int | None) -> str | None:
        if ri is None:
            return None
        out = [
            f"FY{int(yr)} {v:+.0%}"
            for j in range(1, len(rows[ri]))
            if (v := clean_num(rows[ri][j])) is not None
            and j < len(rows[yhdr]) and (yr := clean_num(rows[yhdr][j])) is not None
        ]
        return ", ".join(out[-5:]) if out else None

    parts: list[str] = []
    if (e := series(_find_row_prefix(rows, "EPS (GAAP)"))) is not None:
        parts.append(f"GAAP-EPS surprise: {e}")
    if (rv := series(_find_row(rows, "Revenue"))) is not None:
        parts.append(f"Revenue surprise: {rv}")
    if not parts:
        return Sourced.unknown(note="no EPS/Revenue surprise series in the Surprise sheet")
    return Sourced.present(
        "; ".join(parts) + " (fiscal-year, GAAP-EPS basis — adjusted basis is the 99.1 guide; "
        "+beat / −miss)",
        source_ref="CIQ Estimates→Surprise (annual)",
    )


# --- consensus context: Estimates → Consensus / Revisions -------------------------------------


def _revision_breadth(rows: Rows, metric_block: str) -> str | None:
    """For a metric block (e.g. 'EPS (GAAP)'), the Last-Month Upward/Downward on the FY column."""
    bi = _find_row(rows, metric_block)
    if bi is None or bi + 1 >= len(rows):
        return None
    header = rows[bi + 1]
    fy_col = next(
        (j for j, c in enumerate(header) if isinstance(c, str) and c.strip().startswith("FY")), None
    )
    rng = range(bi, min(bi + 10, len(rows)))
    up = next((i for i in rng if rows[i] and str(rows[i][0]).strip() == "Upward"), None)
    dn = next((i for i in rng if rows[i] and str(rows[i][0]).strip() == "Downward"), None)
    if fy_col is None or up is None or dn is None:
        return None
    u, d = clean_num(rows[up][fy_col]), clean_num(rows[dn][fy_col])
    return f"{metric_block} {str(header[fy_col]).strip()}: {int(u or 0)}↑/{int(d or 0)}↓ last mo"


def _revisions_field(bundle: CiqBundle, metric: str) -> Sourced[str]:
    try:
        rows = bundle.sheet("estimates", "Revisions")
    except CiqUnavailableError as exc:
        return _miss_or_unknown(bundle, "estimates", exc)
    breadth = _revision_breadth(rows, metric)
    if breadth is None:
        return Sourced.unknown(note=f"no '{metric}' revision block in Estimates→Revisions")
    return Sourced.present(breadth, source_ref="CIQ Estimates→Revisions (Last-Month breadth, FY)")


def eps_revisions(bundle: CiqBundle) -> Sourced[str]:
    return _revisions_field(bundle, "EPS (GAAP)")


def revenue_revisions(bundle: CiqBundle) -> Sourced[str]:
    return _revisions_field(bundle, "Revenue")


def consensus_view(bundle: CiqBundle) -> Sourced[str]:
    """Consensus target / LT growth / recommendation (the 'am I non-consensus' context). The two
    columns are mean / median; growth is shown as a percent; the recommendation score is explained
    (CIQ scores 1=buy … 5=sell) — no bare/unlabelled numbers."""
    try:
        rows = bundle.sheet("estimates", "Consensus")
    except CiqUnavailableError as exc:
        return _miss_or_unknown(bundle, "estimates", exc)
    parts: list[str] = []
    tp = _find_row_prefix(rows, "Target Price")
    if tp is not None and len(rows[tp]) > 2:
        mean, med = clean_num(rows[tp][1]), clean_num(rows[tp][2])
        if mean is not None or med is not None:
            parts.append(f"Target price: mean {_usd(mean)} / median {_usd(med)}")
    lg = _find_row_prefix(rows, "LT Growth")
    if lg is not None and len(rows[lg]) > 2:
        mean, med = clean_num(rows[lg][1]), clean_num(rows[lg][2])
        if mean is not None or med is not None:
            parts.append(f"LT growth: mean {_pct1(mean)} / median {_pct1(med)}")
    rec = _find_row_prefix(rows, "Industry Recommend")
    if rec is not None and len(rows[rec]) > 1:
        v = str(rows[rec][1]).strip()
        if v and v not in _UNAVAILABLE_CELLS:
            parts.append(f"Recommendation: {v} (CIQ score, 1=buy … 5=sell)")
    if not parts:
        return Sourced.unknown(note="no Target Price/LT Growth/Recommendation rows in Consensus")
    return Sourced.present("; ".join(parts), source_ref="CIQ Estimates→Consensus")


def _parse_business_relationships(raw: str) -> list[str] | None:
    """Parse the CIQ Business-Relationships export (pipe-delimited RTF text) into readable lines
    'Name — Type · Industry · src: Source'. The table starts at a 'Customer Name|Relationship
    Type|…' header; 'Business Description:' prose rows are skipped. None if no table is found."""
    lines = [ln.strip() for ln in raw.splitlines()]
    hdr = next(
        (i for i, ln in enumerate(lines) if "Customer Name" in ln and "Relationship Type" in ln),
        None,
    )
    if hdr is None:
        return None
    out: list[str] = []
    for ln in lines[hdr + 1 :]:
        if not ln or ln.startswith("Business Description"):
            continue
        cells = [c.strip() for c in ln.split("|") if c.strip()]
        if len(cells) < 3:  # need at least name | type | industry
            continue
        name, rtype, industry = cells[0], cells[1], cells[2]
        line = f"{name} — {rtype} · {industry}"
        if len(cells) > 3:
            line += f" · src: {cells[3]}"
        out.append(line)
    return out or None


def customers(bundle: CiqBundle) -> Sourced[str]:
    """Customer concentration from the CIQ Business-Relationships (.rtf) export — parsed into
    readable lines (name / relationship / industry), not a raw pipe-dump. Fail loud if unparsed."""
    wb = bundle.workbook("customers")
    if wb is None:
        return Sourced.missing(
            note=f"no Customers & Suppliers export for {bundle.ticker} — pull it and re-run"
        )
    try:
        raw = read_text(wb.path, wb.fmt)
    except CiqParseError as exc:
        return Sourced.unknown(note=str(exc))
    parsed = _parse_business_relationships(raw)
    if not parsed:
        return Sourced.unknown(
            note=f"could not parse the Business-Relationships table in {wb.path.name}"
        )
    body = "; ".join(parsed[:30])
    if len(parsed) > 30:
        body += f"; …(+{len(parsed) - 30} more)"
    return Sourced.present(body, source_ref=f"CIQ Customers&Suppliers {wb.path.name}")


# --- transcripts: qualitative context only (no numbers derived) -------------------------------


_TRANSCRIPT_PROSE = ("Call Participants", "Corporate Participants", "Presentation", "Operator")


_CALL_OPEN = re.compile(r"Operator\s+Good\s+(?:morning|afternoon|evening)", re.I)
# the IR's hand-off to management — the boundary between boilerplate and the call's substance.
# "the call"/"it" (not "the presentation", which is the operator→IR hand-off before the legalese).
_HANDOFF = re.compile(r"\b(?:turn|hand)\w*\s+(?:the\s+call|it)\s+(?:over\s+|back\s+)?to\b", re.I)


def _transcript_prose(text: str) -> str:
    """Land on the call's SUBSTANCE — management's prepared remarks onward — skipping CIQ's leading
    S&P estimates table, the dotted table-of-contents, the operator intro, and the forward-looking-
    statements legalese. Anchor at the IR's hand-off to management (after the boilerplate); else
    the operator opening; else the first marker; else the whole text. The machine only WIDENS
    the window — it never picks the 'relevant' passage; the human reads the call and judges."""
    for pat in (_HANDOFF, _CALL_OPEN):
        m = pat.search(text)
        if m is not None:
            return text[m.start() :]
    starts = [i for i in (text.find(k) for k in _TRANSCRIPT_PROSE) if i >= 0]
    return text[min(starts) :] if starts else text


_TRANSCRIPT_CAP = 80_000  # carry the whole call (remarks + Q&A); a runaway bound, not token economy


def management_commentary(bundle: CiqBundle) -> Sourced[str]:
    """Earnings-call transcript as QUALITATIVE context (no numbers computed from it). CIQ ships them
    Word docs renamed .rtf (``ole_disguised``) → the LibreOffice path; UNKNOWN if no converter. The
    boilerplate (estimates table / TOC / operator intro / forward-looking-statements legalese) is
    skipped and the window is WIDE — prepared remarks AND Q&A (the call's substance), surfaced
    in full for the human to read. The machine does not curate the 'relevant' passage."""
    wb = bundle.workbook("transcript")
    if wb is None:
        return Sourced.missing(note=f"no earnings-call transcript for {bundle.ticker} — pull it")
    try:
        text = _transcript_prose(read_text(wb.path, wb.fmt))
    except CiqParseError as exc:
        return Sourced.unknown(note=f"transcript needs LibreOffice/Word conversion: {exc}")
    return Sourced.present(
        text[:_TRANSCRIPT_CAP],
        source_ref=f"CIQ transcript {wb.path.name} (remarks + Q&A; qualitative, no numbers)",
    )
