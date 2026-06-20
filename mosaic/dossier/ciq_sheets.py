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


def margin_trend(bundle: CiqBundle) -> Sourced[str]:
    try:
        rows = bundle.sheet("financials", "Income Statement", freq="annual")
    except CiqUnavailableError as exc:
        return _miss_or_unknown(bundle, "financials", exc)
    hdr = _period_header(rows)
    rev_i, gp_i = _find_row(rows, "Total Revenue"), _find_row(rows, "Gross Profit")
    eb_i = _find_row(rows, "EBITDA")
    if rev_i is None or hdr is None:
        return Sourced.unknown(note="Income Statement missing Total Revenue / period header")
    latest = _latest_col(rows, rev_i, hdr)
    if latest is None:
        return Sourced.unknown(note="no revenue value")
    col, rev, period = latest

    def margin(ri: int | None) -> str:
        v = clean_num(rows[ri][col]) if ri is not None and col < len(rows[ri]) else None
        return f"{v / rev:.0%}" if v is not None and rev else "n/a"

    recl = _reclassified_cols(rows[hdr])
    prior = [j for j in range(1, col) if clean_num(rows[rev_i][j]) is not None]
    yoy = "UNAVAILABLE (no prior-period column)"
    if prior:
        pj = prior[-1]
        lc = rows[hdr][col] if col < len(rows[hdr]) else ""
        lp = rows[hdr][pj] if pj < len(rows[hdr]) else ""
        if _is_ltm(lc) != _is_ltm(lp):  # never compare an LTM column against a fiscal-year one
            yoy = "UNAVAILABLE (LTM-vs-FY period mix)"
        elif (pj in recl) != (col in recl):  # never YoY across a reclassified-basis change
            yoy = "UNAVAILABLE (reclassified-basis boundary)"
        else:
            pv = clean_num(rows[rev_i][pj])
            yoy = f"{rev / pv - 1:+.0%}" if pv else "n/a"
    return Sourced.present(
        f"[{period}] gross {margin(gp_i)}, EBITDA {margin(eb_i)}; revenue YoY {yoy}",
        source_ref="CIQ Financials→Income Statement (margins; YoY respects Reclassified)",
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


def _segment_section(bundle: CiqBundle, section: str) -> Sourced[str]:
    try:
        rows = bundle.sheet("financials", "Segments", freq="annual")
    except CiqUnavailableError as exc:
        return _miss_or_unknown(bundle, "financials", exc)
    hdr = _period_header(rows)
    start = _find_row(rows, section)
    total = next(
        (
            i for i, r in enumerate(rows)
            if r and str(r[0]).strip().startswith(f"Total {section.rstrip('s')}")
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
    return Sourced.present(
        f"[{period}] " + "; ".join(parts) + f" of Total {tot:,.0f}",
        source_ref=f"CIQ Financials→Segments ({section} section, latest annual column)",
    )


def segments(bundle: CiqBundle) -> Sourced[str]:
    """Segment REVENUE mix + each segment's share of total revenue."""
    return _segment_section(bundle, "Revenues")


def segment_ebitda(bundle: CiqBundle) -> Sourced[str]:
    """Segment EBITDA mix + each segment's share of total EBITDA — the decision-relevant view: a
    customer can sit in a segment that is a small share of revenue but a large share of profit."""
    return _segment_section(bundle, "EBITDA")


def geographic(bundle: CiqBundle) -> Sourced[str]:
    try:
        rows = bundle.sheet("financials", "Segments", freq="annual")
    except CiqUnavailableError as exc:
        return _miss_or_unknown(bundle, "financials", exc)
    if not any(r and "geograph" in str(r[0]).lower() for r in rows):
        return Sourced.unknown(note="no geographic breakdown in Segments (likely single-geography)")
    return Sourced.unknown(note="geographic section present; extractor not wired — read by hand")


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


def _transcript_prose(text: str) -> str:
    """Land on the management REMARKS — skip CIQ's leading S&P estimates table AND the dotted
    table-of-contents. Prefer the operator opening the call (the real prepared remarks begin there);
    else the first transcript section marker; else the whole text. Keeps the window qualitative."""
    m = _CALL_OPEN.search(text)
    if m is not None:
        return text[m.start() :]
    starts = [i for i in (text.find(k) for k in _TRANSCRIPT_PROSE) if i >= 0]
    return text[min(starts) :] if starts else text


def management_commentary(bundle: CiqBundle) -> Sourced[str]:
    """Earnings-call transcript as QUALITATIVE context (no numbers computed from it). CIQ ships them
    Word docs renamed .rtf (``ole_disguised``) → the LibreOffice path; UNKNOWN if no converter. The
    leading S&P estimates table is skipped so the surfaced window is prose, not a numbers table."""
    wb = bundle.workbook("transcript")
    if wb is None:
        return Sourced.missing(note=f"no earnings-call transcript for {bundle.ticker} — pull it")
    try:
        text = _transcript_prose(read_text(wb.path, wb.fmt))
    except CiqParseError as exc:
        return Sourced.unknown(note=f"transcript needs LibreOffice/Word conversion: {exc}")
    return Sourced.present(
        text[:1500],
        source_ref=f"CIQ transcript {wb.path.name} (qualitative context only — no numbers derived)",
    )
