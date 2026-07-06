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
import statistics
from collections.abc import Callable
from datetime import date
from typing import Any, NamedTuple

from vinci.dossier.ciq import (
    _UNAVAILABLE_CELLS,
    CiqBundle,
    CiqParseError,
    CiqUnavailableError,
    clean_num,
    excel_date,
    read_text,
)
from vinci.dossier.schemas import (
    CapitalInstrument,
    FinRow,
    FinTable,
    GuidanceRow,
    ImpliedRow,
    ImpliedValuation,
    PeerComps,
    PeerRow,
    RevisionEvent,
    Sourced,
    SourceStatus,
)

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


# ~2y of quarterly closes — below this an own-history floor read is unreliable: it mirrors the P/E
# percentile's ~2y bar (screens/assemble.py), and post-drawdown a handful of closes makes
# "near-floor" near-tautological rather than informative.
_MIN_CONFIDENT_CLOSES = 8


def range_position(bundle: CiqBundle) -> Sourced[str]:
    """Own-history read: current TEV/LTM EBITDA + its trailing low–median–high RANGE and where in
    it, WITH a sample-size confidence label. Below ~2y of closes the floor VERDICT is suppressed (a
    floor read on a handful of points is unreliable and near-tautological post-drawdown)."""
    try:
        rows = bundle.sheet("financials", "Multiples", freq="quarterly")
    except CiqUnavailableError as exc:
        return _miss_or_unknown(bundle, "financials", exc)
    ev_pairs = [(d, v) for d, v in _multiples_close(rows, "TEV/LTM EBITDA") if v is not None]
    pe = [v for _, v in _multiples_close(rows, "P/LTM EPS") if v is not None]
    if len(ev_pairs) < 4:
        return Sourced.unknown(note="TEV/LTM EBITDA Close has <4 quarters — no range position")
    ev = [v for _, v in ev_pairs]
    cur, hist = ev[-1], ev[:-1]
    cur_date = ev_pairs[-1][0]
    lo, hi, med = min(hist), max(hist), statistics.median(hist)
    pct = sum(1 for h in hist if h <= cur) / len(hist)
    if len(hist) < _MIN_CONFIDENT_CLOSES:
        where = (
            f"LOW-CONFIDENCE ({len(hist)} closes < {_MIN_CONFIDENT_CLOSES}q ≈2y) — floor read "
            "unreliable"
        )
    else:
        band = next(b for t, b in _RANGE_BANDS if pct <= t)
        where = f"{pct:.0%}ile → {band}"
    asof = f" as-of {cur_date.isoformat()}" if cur_date is not None else ""
    tail = f"; P/LTM EPS {pe[-1]:.1f}x" if pe else ""
    return Sourced.present(
        f"EV/EBITDA (TEV/LTM) {cur:.1f}x{asof} — trailing range {lo:.1f}–{hi:.1f}x "
        f"(median {med:.1f}x) over {len(hist)} closes → {where}{tail}",
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


def ev_ebitda_asof(bundle: CiqBundle) -> date | None:
    """The DATE of the latest TEV/LTM EBITDA Close that ``ev_ebitda_current`` reports — so the
    caller can judge whether that 'current' multiple is stale (its last Close predates the assembly
    reference date). None when the Multiples sheet / a dated close is absent."""
    try:
        rows = bundle.sheet("financials", "Multiples", freq="quarterly")
    except CiqUnavailableError:
        return None
    closes = _multiples_close(rows, "TEV/LTM EBITDA")
    dated = [d for d, v in closes if v is not None and d is not None]
    return dated[-1] if dated else None


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


def _bs_period_header(rows: Rows) -> int | None:
    """The CIQ Balance Sheet period row is labelled 'Balance Sheet as of:' (not 'Fiscal Period'), so
    the generic header finder misses it and the period would render blank — find it explicitly."""
    return next((i for i, r in enumerate(rows) if r and "as of" in str(r[0]).lower()), None)


def _bs_latest(bundle: CiqBundle, label: str) -> Sourced[float]:
    """Latest value ($M) of a CIQ Balance Sheet line, freshest period first — tries the QUARTERLY
    sheet's row, then the ANNUAL sheet's (so label drift that drops the row from one granularity
    doesn't fall through to the EDGAR breadth figure). The Balance Sheet carries CIQ's own
    classified 'Total Debt'/'Net Debt' totals — the depth-stage authority the partial EDGAR-XBRL
    tags under-capture."""
    def pick(rows: Rows) -> Sourced[float] | None:
        ri = _find_row(rows, label)
        if ri is None:
            return None
        latest = _latest_col(rows, ri, _bs_period_header(rows))
        if latest is None:
            return None
        _, value, period = latest
        suffix = f" [{period}]" if period else " [latest]"
        return Sourced.present(
            round(value, 1), source_ref=f"CIQ Financials→Balance Sheet '{label}'{suffix}"
        )

    seen = False
    unavailable: Exception | None = None
    try:  # literal freqs (not a loop var) so the CIQ-manifest drift guard can see the address
        rows = bundle.sheet("financials", "Balance Sheet", freq="quarterly")
        seen = True
        if (got := pick(rows)) is not None:
            return got
    except CiqUnavailableError as exc:
        unavailable = exc
    try:
        rows = bundle.sheet("financials", "Balance Sheet", freq="annual")
        seen = True
        if (got := pick(rows)) is not None:
            return got
    except CiqUnavailableError as exc:
        unavailable = exc
    if not seen:
        assert unavailable is not None  # neither sheet loaded — workbook or both sheets absent
        return _miss_or_unknown(bundle, "financials", unavailable)
    return Sourced.unknown(note=f"Balance Sheet has no '{label}' row (quarterly or annual)")


def net_debt(bundle: CiqBundle) -> Sourced[float]:
    """CIQ Net Debt ($M) — classified total debt minus cash & ST investments. The depth-stage
    authority for leverage on a finalist; EDGAR-XBRL net-debt under-captures scattered instrument
    debt (convertible / notes / short-term / subordinated tags) and can flip to a false net-cash."""
    return _bs_latest(bundle, "Net Debt")


def total_debt(bundle: CiqBundle) -> Sourced[float]:
    """CIQ gross Total Debt ($M) — the classified balance-sheet total, for context alongside net."""
    return _bs_latest(bundle, "Total Debt")


def ltm_ebitda(bundle: CiqBundle) -> Sourced[float]:
    """Latest consolidated EBITDA ($M) — the rightmost valued column of the Income Statement
    'EBITDA' row (LTM/TTM if the workbook carries one, else the latest FY): the net-debt/EBITDA
    denominator paired with CIQ Net Debt. Fail-loud UNKNOWN if the row is absent or empty."""
    try:
        rows = bundle.sheet("financials", "Income Statement", freq="annual")
    except CiqUnavailableError as exc:
        return _miss_or_unknown(bundle, "financials", exc)
    ri = _find_row(rows, "EBITDA")
    if ri is None:
        return Sourced.unknown(note="Income Statement sheet has no 'EBITDA' row")
    latest = _latest_col(rows, ri, _period_header(rows))
    if latest is None:
        return Sourced.unknown(note="EBITDA row has no value in any period")
    _, value, period = latest
    return Sourced.present(
        round(value, 1), source_ref=f"CIQ Financials→Income Statement 'EBITDA' [{period}]"
    )


def ltm_ocf(bundle: CiqBundle) -> Sourced[float]:
    """Latest operating cash flow ($M) — the rightmost valued column of the Cash Flow 'Cash from
    Ops.' row (LTM/TTM when present, else latest FY). The net-debt/OCF denominator paired with CIQ
    Net Debt; OCF carries the D&A add-back so it survives an untaggable-EBITDA name. Fail-loud
    UNKNOWN if the row is absent or empty."""
    try:
        rows = bundle.sheet("financials", "Cash Flow", freq="annual")
    except CiqUnavailableError as exc:
        return _miss_or_unknown(bundle, "financials", exc)
    ri = _find_row(rows, "Cash from Ops.")
    if ri is None:
        return Sourced.unknown(note="Cash Flow sheet has no 'Cash from Ops.' row")
    latest = _latest_col(rows, ri, _period_header(rows))
    if latest is None:
        return Sourced.unknown(note="'Cash from Ops.' has no value in any period")
    _, value, period = latest
    return Sourced.present(
        round(value, 1), source_ref=f"CIQ Financials→Cash Flow 'Cash from Ops.' [{period}]"
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
    """The MARGIN trajectory — gross and EBITDA margin (%) per period — PAIRED in the same field
    with the ABSOLUTE EBITDA + revenue trajectory, so margin compression is never shown without its
    disconfirming context (VRRM: ~42%→37% margin WHILE EBITDA 229→362 — consensus misreads the
    falling % as a bear; the absolute EBITDA RISING is the real signal). Each margin is a ratio
    within one column, so the Reclassified basis (marked) is never crossed."""
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

    eb_i = _find_row(rows, "EBITDA")
    eb_traj = margin_traj(eb_i)
    gp_traj = margin_traj(_find_row(rows, "Gross Profit"))
    if eb_traj is None and gp_traj is None:
        return Sourced.unknown(note="no gross/EBITDA margin series in the Income Statement")
    bits = [f"EBITDA margin: {eb_traj}"] if eb_traj else []
    if gp_traj:
        bits.append(f"gross margin: {gp_traj}")
    # PAIR the margin % with its RECONCILER — absolute EBITDA + revenue — in the SAME field, so the
    # % is never read alone (a margin % can FALL while absolute EBITDA RISES: scaling, not decline).
    # Emitted as clean ';'-separated series so the table renderer parses each as its own row.
    abs_eb = _trajectory_row(rows, eb_i, hdr)
    abs_rev = _trajectory_row(rows, rev_i, hdr)
    if abs_eb:
        bits.append(f"absolute EBITDA: {abs_eb}")
    if abs_rev:
        bits.append(f"absolute revenue: {abs_rev}")
    return Sourced.present(
        "; ".join(bits)
        + "  [R reclassified; margin % can fall while absolute EBITDA RISES — read them together]",
        source_ref="CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)",
    )


def liquidity_covenant_flags(bundle: CiqBundle) -> Sourced[str]:
    try:
        rows = bundle.sheet("financials", "Capital Structure Details", freq="annual")
    except CiqUnavailableError as exc:
        return _miss_or_unknown(bundle, "financials", exc)
    hdr = _find_row(rows, "Description")  # the latest FY section's instrument table
    if hdr is None:
        return Sourced.unknown(note="Capital Structure Details has no instrument table")
    # locate the 'Maturity' column by its header LABEL — column order is not contractually fixed
    # (ciq_extraction_notes rule #4), so a hardcoded index could read a coupon/price as a date.
    mat_col = next((j for j, c in enumerate(rows[hdr]) if str(c).strip() == "Maturity"), None)
    insts: list[str] = []
    for i in range(hdr + 1, min(hdr + 12, len(rows))):
        desc = str(rows[i][0]).strip()
        if not desc or desc.startswith("FY ") or desc == "Description":
            break
        typ = str(rows[i][1]).strip() if len(rows[i]) > 1 else ""
        principal = clean_num(rows[i][2]) if len(rows[i]) > 2 else None
        coupon = str(rows[i][3]).strip() if len(rows[i]) > 3 else ""
        # 'Maturity' is a serial OR a date string — excel_date handles both (clean_num would kill a
        # date string). Plausibility-bound the year so a mis-parsed cell can't fabricate 'Due 1900'.
        mdate = (
            excel_date(rows[i][mat_col])
            if mat_col is not None and mat_col < len(rows[i]) else None
        )
        amt = f"{principal:,.0f}" if principal is not None else "undrawn/–"
        due = f" Due {mdate.year}" if (mdate and 2000 <= mdate.year <= 2100) else ""
        insts.append(f"{desc} ({typ}) {amt} @ {coupon}{due}")
    if not insts:
        return Sourced.unknown(note="no debt instruments parsed")
    return Sourced.present("; ".join(insts), source_ref="CIQ Financials→Capital Structure Details")


# --- E1: STRUCTURED capital structure (instruments + summary aggregates) -----------------------
_CS_COLS = (  # Details-panel columns, located by header LABEL (order not contractually fixed)
    "Description", "Type", "Principal Due", "Coupon", "Floating Rate", "Maturity",
    "Seniority", "Secured", "Convertible", "Repayment Curren",
)


def _cs_detail_asof(rows: Rows) -> str:
    """The Details panel's own filing note ('A 2025 filed Mar-16-2026') — the DETAIL is panel-dated,
    so this is the detail-as-of (distinct from the latest-quarter total debt for reconciliation)."""
    for r in rows[:12]:
        for j, c in enumerate(r):
            if str(c).strip().rstrip(":") == "Source" and j + 1 < len(r):
                v = str(r[j + 1]).strip()
                if v:
                    return v
    return ""


def _capital_summary(bundle: CiqBundle) -> Sourced[str]:
    """(E1) Capital-Structure-Summary aggregates (latest quarter) + the term-loan QoQ movement — the
    reconciliation anchor: the itemized detail is panel-dated, the total debt is latest-quarter."""
    try:
        s = bundle.sheet("financials", "Capital Structure Summary", freq="annual")
    except CiqUnavailableError:
        return Sourced.unknown(note="Capital Structure Summary: unavailable")
    hdrs = [r for r in s if r and "Fiscal Peri" in str(r[0])]
    vcols = [j for j in range(1, len(hdrs[-1]))
             if "months" in str(hdrs[-1][j]).lower()] if hdrs else []
    if len(vcols) < 1:
        return Sourced.unknown(note="Capital Structure Summary: no period columns")

    def at(prefix: str, col: int) -> float | None:
        i = _find_row_prefix(s, prefix)
        return clean_num(s[i][col]) if i is not None and col < len(s[i]) else None

    parts: list[str] = []
    tl = at("Total Term Loans", vcols[-1])
    tlp = at("Total Term Loans", vcols[-2]) if len(vcols) > 1 else None
    if tl is not None:
        qoq = f" ({tlp:,.1f}→{tl:,.1f} QoQ)" if tlp is not None else ""
        parts.append(f"term loans {tl:,.1f}{qoq}")
    for prefix, disp in (("Total Senior Bonds", "senior bonds"), ("Total Lease", "leases"),
                         ("Total Principal Due", "total principal")):
        v = at(prefix, vcols[-1])
        if v is not None:
            parts.append(f"{disp} {v:,.1f}")
    td = at("Total Debt Outstanding", vcols[-1]) or at("Total Debt", vcols[-1])
    if td is not None:
        parts.append(f"total debt {td:,.1f} (latest quarter)")
    if not parts:
        return Sourced.unknown(note="Capital Structure Summary: no aggregates parsed")
    return Sourced.present(
        "; ".join(parts) + " ($M)", source_ref="CIQ Financials→Capital Structure Summary")


def capital_structure_ciq(
    bundle: CiqBundle,
) -> tuple[Sourced[list[CapitalInstrument]], Sourced[str], str]:
    """(E1) Structured capital structure from CIQ Financials→Capital Structure Details — the LATEST
    per-fiscal-period panel, parsed by header LABEL (not a fixed index) — plus the Summary
    aggregates. Returns (instruments, summary-line, detail-as-of). Maturity is decoded from the
    serial to an ISO date, or None when the panel gives '-' (undated)."""
    try:
        det = bundle.sheet("financials", "Capital Structure Details", freq="annual")
    except CiqUnavailableError as exc:
        u: Sourced[Any] = _miss_or_unknown(bundle, "financials", exc)
        return u, u, ""
    hdr = _find_row(det, "Description")
    if hdr is None:
        u2: Sourced[Any] = Sourced.unknown(note="Capital Structure Details: no instrument table")
        return u2, u2, ""
    # normalise the non-breaking space CIQ uses in some headers ('Floating\xa0Rate') before matching
    def _norm(c: Any) -> str:
        return str(c).replace("\xa0", " ").strip()

    col = {
        name: next((j for j, c in enumerate(det[hdr]) if _norm(c).startswith(name)), None)
        for name in _CS_COLS
    }
    detail_as_of = _cs_detail_asof(det)
    insts: list[CapitalInstrument] = []
    for i in range(hdr + 1, len(det)):
        desc = str(det[i][0]).strip()
        if not desc or desc == "Description" or desc.startswith("FY "):
            break

        def cell(name: str, ri: int = i) -> str:
            j = col[name]
            return str(det[ri][j]).strip() if j is not None and j < len(det[ri]) else ""

        mat_j, prin_j = col["Maturity"], col["Principal Due"]
        mdate = excel_date(det[i][mat_j]) if mat_j is not None and mat_j < len(det[i]) else None
        principal = (clean_num(det[i][prin_j])
                     if prin_j is not None and prin_j < len(det[i]) else None)
        insts.append(CapitalInstrument(
            description=desc, type=cell("Type"), principal_musd=principal,
            coupon=cell("Coupon"), floating_rate=cell("Floating Rate"),
            maturity_date=(mdate.isoformat() if mdate and 2000 <= mdate.year <= 2100 else None),
            seniority=cell("Seniority"), secured=cell("Secured").lower() == "yes",
            convertible="convert" in cell("Convertible").lower(),
            currency=cell("Repayment Curren"),
        ))
    if not insts:
        u3: Sourced[Any] = Sourced.unknown(note="Capital Structure Details: no instruments parsed")
        return u3, u3, detail_as_of
    instruments = Sourced.present(
        insts, source_ref=f"CIQ Financials→Capital Structure Details ({detail_as_of})")
    return instruments, _capital_summary(bundle), detail_as_of


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
        "; ".join(parts) + " (GAAP-EPS basis; +beat / −miss)",
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


# --- catalyst path: the five previously-unparsed Estimates sheets (Revisions windows / Trends /
# --- Guidance / Multiples / Recent Changes) — horizon-matched, native-cadence, no conclusions.
#
# Metric block labels observed in Trends/Revisions (Company-Level rows); absent ones are simply
# skipped by the exact-match _find_row (never positionally guessed). "scan for more" per the notes.
_METRICS: tuple[str, ...] = (
    "Revenue", "EBITDA", "EBIT", "EBT (GAAP)", "EPS Normalized", "EPS (GAAP)",
    "Net Income (GAAP)", "Net Income (Excl. Excep)", "Interest Expense",
)
_GUIDANCE_METRICS: tuple[str, ...] = (
    "Revenue", "Capital Expenditure", "Gross Margin %", "EBITDA", "EPS Normalized",
)
_REV_WINDOWS: tuple[tuple[str, str], ...] = (
    ("1m", "Last Month"), ("2m", "Last 2 Months"), ("3m", "Last 3 Months"),
)
# Trends snapshot row label → lookback in months (CIQ's fixed cadence). Ragged by design: a block
# renders only the snapshots actually present — a hole is labelled n/a, NEVER interpolated.
_SNAP_LOOKBACK: dict[str, int] = {
    "Current": 0, "1 month ago": 1, "2 months ago": 2, "3 months ago": 3,
    "6 months ago": 6, "9 months ago": 9, "12 months ago": 12,
}
_LOOKBACK_ORDER: tuple[tuple[str, int], ...] = (
    ("12m", 12), ("9m", 9), ("6m", 6), ("3m", 3), ("2m", 2), ("1m", 1), ("now", 0),
)
_MULT_LADDER_ROWS: tuple[str, ...] = (
    "NTM", "FY 2026", "FY 2027", "FY 2028", "FY 2029", "FY 2030", "FY 2031", "FY 2032", "FY 2033",
)


def _fig(v: float) -> str:  # a consensus figure → 1 decimal at scale, 2 for small (EPS) — no faking
    return f"{v:,.1f}" if abs(v) >= 10 else f"{v:,.2f}"


def _lookback_lbl(months: int, floor: bool = False) -> str:
    """A CIQ snapshot lookback → label. ALWAYS months-before-EXPORT (never calendar-resolved). On a
    floor basis (export date unverified) the newest snapshot reads 'latest', not 'now' — 'now' would
    imply a known calendar anchor the floor does not have."""
    if months == 0:
        return "latest" if floor else "now"
    return f"{months}m"


def _is_floor(as_of: str | None) -> bool:
    """True when the as-of is a FLOOR (export date unverified) — carried as a '≥'-prefixed value."""
    return bool(as_of and as_of.startswith("≥"))


def _asof_suffix(as_of: str | None) -> str:
    if not as_of:
        return ""
    if _is_floor(as_of):
        return f"  [data ≥ {as_of[1:]} · export date unverified]"
    return f"  [as-of {as_of}]"


def _net_change(first: float, last: float) -> str:
    """Sign-aware net-change phrase for a consensus path. A strictly-positive series → a signed %; a
    negative or zero-crossing series → DIRECTION words, never a bare signed % (which misreads a
    shrinking expense −13.7→−4.9 as a −64% 'decline' when it is an improvement)."""
    if first > 0 and last > 0:
        return f"net {(last / first - 1) * 100:+.0f}%"
    if first < 0 and last < 0:
        if abs(last) < abs(first):
            return "improving (magnitude toward zero)"
        if abs(last) > abs(first):
            return "worsening (magnitude away from zero)"
        return "flat"
    if last > first:
        return "improving (crossed zero)"
    if last < first:
        return "worsening (crossed zero)"
    return "flat"


def _scan_asof_header(rows: Rows) -> date | None:
    """A decoded date from an explicit 'As-Of Date:' cell in a sheet's metadata rows (the sibling
    comps book carries one on every sheet). Matched by LABEL, never positionally. None if absent."""
    for r in rows[:14]:
        for j, c in enumerate(r):
            if isinstance(c, str) and c.strip().rstrip(":").strip().lower() == "as-of date":
                d = excel_date(r[j + 1]) if j + 1 < len(r) else None
                if d is not None:
                    return d
    return None


def _parse_range(cell: Any) -> tuple[float, float] | None:
    """A CIQ guidance range string → (low, high); parentheses mean NEGATIVE ("(120.00)" → -120.0);
    a bare point ("427.516") → (v, v). None when not numeric ("-"/empty). The verbatim string is
    kept in the source_ref by the caller — this only parses the bounds."""
    s = str(cell).strip()
    if not s or s in _UNAVAILABLE_CELLS:
        return None

    def _one(tok: str) -> float | None:
        tok = tok.strip()
        neg = tok.startswith("(") and tok.endswith(")")
        try:
            v = float(tok.strip("()").replace(",", ""))
        except ValueError:
            return None
        return -v if neg else v

    if " - " in s:
        lo_s, hi_s = s.split(" - ", 1)
        lo, hi = _one(lo_s), _one(hi_s)
        return (min(lo, hi), max(lo, hi)) if lo is not None and hi is not None else None
    v = _one(s)
    return (v, v) if v is not None else None


def _recent_changes_rows(rows: Rows) -> tuple[int, Rows] | None:
    """(header_index, event_rows) for Recent Changes, matched by the 'Change Type' header (the sheet
    leads with blank spacer rows). None if the header is absent."""
    hi = _find_row(rows, "Change Type")
    if hi is None:
        return None
    return hi, [r for r in rows[hi + 1:] if r and str(r[0]).strip()]


def _metric_block_header(rows: Rows, bi: int) -> list[Any] | None:
    """The period-column header row for a Trends/Revisions metric block at ``bi`` — the nearby row
    carrying FQ…/FY… period labels (the 'NasdaqCM:…'/'Company Level' row)."""
    for k in range(bi + 1, min(bi + 4, len(rows))):
        if any(isinstance(c, str) and c.strip().startswith(("FQ", "FY")) for c in rows[k]):
            return rows[k]
    return None


def _first_fy_col(header: list[Any]) -> int | None:
    """The current-fiscal-year column — the FIRST 'FY …' period in the header."""
    return next(
        (j for j, c in enumerate(header) if isinstance(c, str) and c.strip().startswith("FY")), None
    )


def _first_fq_cols(header: list[Any], n: int = 2) -> list[int]:
    """The next-N fiscal-quarter columns — the FIRST n 'FQ …' periods (the 180d verdict window)."""
    fq = [j for j, c in enumerate(header) if isinstance(c, str) and c.strip().startswith("FQ")]
    return fq[:n]


def _nearest_period_header(rows: Rows, bi: int) -> list[Any] | None:
    """The FY/FQ period header governing a Guidance metric block — the nearest such row above
    ``bi``, else the sheet's first period-header row."""
    for k in range(bi - 1, max(-1, bi - 6), -1):
        if rows[k] and any(
            isinstance(c, str) and c.strip().startswith(("FY", "FQ")) for c in rows[k]
        ):
            return rows[k]
    return next(
        (
            r for r in rows
            if r and any(isinstance(c, str) and c.strip().startswith(("FY", "FQ")) for c in r)
        ),
        None,
    )


def _metric_starts(rows: Rows, metrics: tuple[str, ...]) -> list[int]:
    """Row indices where a metric block begins, in sheet order (exact-label match, never
    positional). Absent metrics are skipped — ragged availability is by design."""
    starts = [bi for m in metrics if (bi := _find_row(rows, m)) is not None]
    return sorted(starts)


def _snapshot_path(rows: Rows, bi: int, col: int) -> list[tuple[int, float]]:
    """Present (lookback_months, value) Trends snapshots for the block at ``bi`` on column ``col``,
    sorted OLDEST→newest. Only snapshots actually present are returned; a present-but-empty ('-') or
    absent lookback is dropped, never interpolated. Stops at the next metric / a repeated lookback
    (a second sub-series)."""
    out: list[tuple[int, float]] = []
    seen: set[int] = set()
    for k in range(bi + 1, min(bi + 18, len(rows))):
        lbl = str(rows[k][0]).strip() if rows[k] else ""
        if lbl in _SNAP_LOOKBACK:
            lb = _SNAP_LOOKBACK[lbl]
            if lb in seen:
                break
            seen.add(lb)
            v = clean_num(rows[k][col]) if col < len(rows[k]) else None
            if v is not None:
                out.append((lb, v))
        elif lbl and k > bi + 1 and not lbl.startswith(("Company Level", "NasdaqCM")):
            break
    out.sort(key=lambda t: -t[0])
    return out


def _estimates_header_asof(bundle: CiqBundle) -> date | None:
    """An EXPLICIT 'As-Of Date:' header from the Estimates export (as the sibling comps book carries
    on every sheet), scanned by LABEL — never positional. None when absent: the observed MVST
    Estimates export has NO such stamp, so the caller falls back to a dated FLOOR. Checks the
    Consensus sheet's metadata rows; a CIQ export that stamps its as-of does so uniformly."""
    try:
        rows = bundle.sheet("estimates", "Consensus")
    except CiqUnavailableError:
        return None
    return _scan_asof_header(rows)


def estimates_as_of(bundle: CiqBundle) -> Sourced[str]:
    """The workbook's as-of date. PREFER an explicit 'As-Of Date:' header (as the sibling comps book
    carries); the observed MVST Estimates export has NONE, so fall back to a dated FLOOR — the max
    Recent-Changes event date — carried as a ``≥``-prefixed value + floor note. A floor is never
    presented as a plain as-of: the true export is on/after it (Trends '1 month ago' already shows
    the latest event; a dated sibling CIQ export in the same pull is weeks newer). Staleness then
    emits a soft 'as-of unverifiable' caveat instead of a false pass, and lookbacks stay
    export-relative."""
    header = _estimates_header_asof(bundle)
    if header is not None:
        return Sourced.present(
            header.isoformat(),
            source_ref="CIQ Estimates→Consensus 'As-Of Date' header (workbook as-of)",
        )
    sidecar = _sidecar_as_of(bundle)  # R1: operator-attested date, precedence above the floor
    if sidecar is not None:
        return Sourced.present(
            sidecar.isoformat(),
            source_ref="operator AS_OF sidecar (data/manual/ciq/<TICKER>/AS_OF)",
            note="operator-attested",
        )
    try:
        rows = bundle.sheet("estimates", "Recent Changes")
    except CiqUnavailableError as exc:
        return _miss_or_unknown(bundle, "estimates", exc)
    rc = _recent_changes_rows(rows)
    latest: date | None = None
    if rc is not None:
        for r in rc[1]:
            d = excel_date(r[1]) if len(r) > 1 else None
            if d is not None and (latest is None or d > latest):
                latest = d
    if latest is None:
        return Sourced.unknown(note="no As-Of header and no dated events in Estimates")
    return Sourced.present(
        f"≥{latest.isoformat()}",
        source_ref="CIQ Estimates→Recent Changes (latest embedded event — export date NOT stamped)",
        note="export date unverified — a FLOOR (data on/after the latest embedded event); the true "
        "export is later (a dated sibling CIQ export in the same pull is weeks newer)",
    )


def acceleration_read(bundle: CiqBundle, *, as_of: str | None = None) -> Sourced[str]:
    """(b) ACCELERATION READ — per-metric current-FY consensus PATH from Trends, across the
    snapshots actually present (Current / N-months-ago), oldest→newest, with the net change. Ragged:
    absent lookbacks are labelled n/a, never interpolated; a block with <2 snapshots renders
    level-only (no 'path'). This surfaces the Edge-2 'stabilizing vs accelerating' evidence the old
    FY-only breadth line hid (MVST FY26 EBITDA 146.5 → 62.1)."""
    try:
        rows = bundle.sheet("estimates", "Trends")
    except CiqUnavailableError as exc:
        return _miss_or_unknown(bundle, "estimates", exc)
    floor = _is_floor(as_of)
    lines: list[str] = []
    for bi in _metric_starts(rows, _METRICS):
        metric = str(rows[bi][0]).strip()
        header = _metric_block_header(rows, bi)
        fy = _first_fy_col(header) if header else None
        if header is None or fy is None:
            continue
        fy_label = str(header[fy]).strip()
        path = _snapshot_path(rows, bi, fy)
        if not path:
            continue
        if len(path) < 2:
            lb, val = path[0]
            at = _lookback_lbl(lb, floor)
            lines.append(f"{fy_label} {metric}: {_fig(val)} ({at}) — level only")
            continue
        chain = " → ".join(f"{_fig(v)} ({_lookback_lbl(lb, floor)})" for lb, v in path)
        oldest, newest = path[0][0], path[-1][0]
        # sign-aware: a bare signed % misreads a negative/zero-crossing series (see _net_change).
        change = _net_change(path[0][1], path[-1][1])
        span = f"{_lookback_lbl(oldest, floor)}→{_lookback_lbl(newest, floor)}"
        present = {lb for lb, _ in path}
        # note only INTERIOR holes (a lookback missing BETWEEN the oldest and newest present ones);
        # a lookback absent only at the recent end is disclosed by the span, not a fabricated gap.
        gaps = [lbl for lbl, lb in _LOOKBACK_ORDER if newest < lb < oldest and lb not in present]
        gap_note = f" [{', '.join(gaps)} n/a]" if gaps else ""
        lines.append(f"{fy_label} {metric}: {chain}; {change} ({span}){gap_note}")
    if not lines:
        return Sourced.unknown(note="no current-FY consensus snapshots in Estimates→Trends")
    # join metric entries with ' | ' (NOT '; ' — each entry uses '; ' internally between chain and
    # net-change, so ' | ' keeps entries cleanly separable for the metric×lookback table render).
    return Sourced.present(
        " | ".join(lines) + _asof_suffix(as_of),
        source_ref="CIQ Estimates→Trends (current-FY consensus path; ragged, absent lookbacks n/a)",
    )


def trends_fy_level(bundle: CiqBundle, *, metric: str, fy_label: str) -> float | None:
    """(H7) The LATEST Trends consensus snapshot for a metric at a SPECIFIC fiscal-year column —
    e.g. ``metric="EBITDA", fy_label="FY 2027"`` → the newest FY2027 EBITDA estimate. This is the
    DIRECT consensus level (the single source of truth for the G anchors), NOT a price-inverted
    ``TEV ÷ multiple`` derivation. None when the sheet/metric/column/snapshot is absent (fail-loud —
    the caller renders n/a, never a fabricated level). Reads the newest present snapshot of the
    block's column; ``acceleration_read`` reads only the FIRST FY column, so this covers next-FY."""
    try:
        rows = bundle.sheet("estimates", "Trends")
    except CiqUnavailableError:
        return None
    bi = _find_row(rows, metric)
    if bi is None:
        return None
    header = _metric_block_header(rows, bi)
    if header is None:
        return None
    col = next((j for j, c in enumerate(header)
                if isinstance(c, str) and c.strip() == fy_label), None)
    if col is None:
        return None
    path = _snapshot_path(rows, bi, col)  # oldest→newest
    return path[-1][1] if path else None  # the newest (latest) snapshot value


def _revisions_windows(rows: Rows, bi: int, end: int) -> dict[str, dict[str, int]]:
    """For a Revisions metric block [bi, end): {window(1m/2m/3m): {'Upward'|'Downward': row_index}}
    — each window's own Upward/Downward rows located by label, never positionally."""
    windows: dict[str, dict[str, int]] = {}
    cur: str | None = None
    for k in range(bi + 1, end):
        lbl = str(rows[k][0]).strip() if rows[k] else ""
        wk = next((w for w, name in _REV_WINDOWS if lbl == name), None)
        if wk is not None:
            cur = wk
            windows[wk] = {}
        elif cur is not None and lbl in ("Upward", "Downward"):
            windows[cur][lbl] = k
    return windows


def horizon_read(bundle: CiqBundle, *, as_of: str | None = None) -> Sourced[str]:
    """(a) HORIZON READ (FQ — the 180d verdict window): per metric, the next-2-FQ revision breadth
    across ALL THREE windows (1m/2m/3m Upward↑/Downward↓). This is the quarterly grid the old
    FY-only Last-Month line hid — e.g. the 2-month-window downward revisions on near quarters."""
    try:
        rows = bundle.sheet("estimates", "Revisions")
    except CiqUnavailableError as exc:
        return _miss_or_unknown(bundle, "estimates", exc)
    starts = _metric_starts(rows, _METRICS)
    lines: list[str] = []
    for idx, bi in enumerate(starts):
        end = starts[idx + 1] if idx + 1 < len(starts) else len(rows)
        metric = str(rows[bi][0]).strip()
        header = _metric_block_header(rows, bi)
        windows = _revisions_windows(rows, bi, end)
        fqs = _first_fq_cols(header) if header else []
        if not header or not fqs or not windows:
            continue
        for col in fqs:
            period = str(header[col]).strip()
            parts: list[str] = []
            for wk, _name in _REV_WINDOWS:
                w = windows.get(wk)
                if not w:
                    continue
                up = _cell_at(rows, w.get("Upward"), col)
                dn = _cell_at(rows, w.get("Downward"), col)
                if up is None and dn is None:
                    continue
                parts.append(f"{wk} {int(up or 0)}↑/{int(dn or 0)}↓")
            if parts:
                lines.append(f"{metric} {period}: " + ", ".join(parts))
    if not lines:
        return Sourced.unknown(note="no next-2-FQ revision breadth in Estimates→Revisions")
    return Sourced.present(
        "; ".join(lines) + _asof_suffix(as_of),
        source_ref="CIQ Estimates→Revisions (next-2-FQ breadth; 1m/2m/3m Upward/Downward)",
    )


def _cell_at(rows: Rows, ri: int | None, col: int) -> float | None:
    return clean_num(rows[ri][col]) if ri is not None and col < len(rows[ri]) else None


def cross_name_anchor(bundle: CiqBundle, *, as_of: str | None = None) -> Sourced[str]:
    """(c) CROSS-NAME ANCHOR (NTM) — the forward-multiple ladder from Estimates→Multiples: NTM +
    FY26→FY33 across TEV/REV · TEV/EBITDA · TEV/EBIT · P/E · PEG ("-" → absent). The cross-sectional
    read the human anchors against peers; the machine assembles the ladder, never a fair value."""
    try:
        rows = bundle.sheet("estimates", "Multiples")
    except CiqUnavailableError as exc:
        return _miss_or_unknown(bundle, "estimates", exc)
    hi = next(
        (i for i, r in enumerate(rows) if any(isinstance(c, str) and "TEV/REV" in c for c in r)),
        None,
    )
    if hi is None:
        return Sourced.unknown(note="no TEV/REV multiple header in Estimates→Multiples")
    hdr = rows[hi]
    cols = [(j, str(hdr[j]).strip()) for j in range(1, len(hdr)) if str(hdr[j]).strip()]
    lines: list[str] = []
    for label in _MULT_LADDER_ROWS:
        ri = _find_row(rows, label)
        if ri is None:
            continue
        cells = []
        any_val = False
        for j, name in cols:
            v = clean_num(rows[ri][j]) if j < len(rows[ri]) else None
            if v is not None:
                any_val = True
            cells.append(f"{name} {v:.2f}" if v is not None else f"{name} –")
        if any_val:
            lines.append(f"{label}: " + " · ".join(cells))
    if not lines:
        return Sourced.unknown(note="no NTM/FY multiple ladder rows in Estimates→Multiples")
    return Sourced.present(
        " | ".join(lines) + _asof_suffix(as_of),
        source_ref="CIQ Estimates→Multiples (forward-multiple ladder: NTM + FY26→FY33)",
    )


def _guidance_rows(rows: Rows, bi: int, end: int) -> tuple[int | None, int | None, int | None]:
    """(guidance-date, guidance-range, actual) row indices for a Guidance metric block [bi, end).
    The As-Of 'Guidance Date'/'Guidance' rows precede the 'Actual/Latest' sub-block; 'Actual' is the
    resolved outcome under it."""

    def find(label: str, lo: int, hi: int) -> int | None:
        return next(
            (k for k in range(lo, hi) if rows[k] and str(rows[k][0]).strip() == label), None
        )

    actual_hdr = find("Actual/Latest", bi, end)
    gdate = find("Guidance Date", bi, actual_hdr or end)
    guide = find("Guidance", bi, actual_hdr or end)
    actual = find("Actual", actual_hdr if actual_hdr is not None else bi, end)
    return gdate, guide, actual


class _GuidanceRead(NamedTuple):
    """The per-metric guidance read the string AND the table both format from (single source, no
    drift). Raw values; each formatter derives its own display (age phrasing, record phrasing)."""

    metric: str
    guide: str  # the guide display (numeric for a point, verbatim quoted for a range)
    period: str  # the fiscal period the latest guide is FOR
    dated: date  # the latest guide's date
    stale_days: int | None  # days old when older than stale_after_days (else None = fresh)
    cost_like: bool  # a spend/cost guide (met when spend ≤ ceiling) vs revenue-like (≥ floor)
    resolved: int  # periods with both a range AND an actual
    met_n: int  # of those, how many met
    recent_period: str | None  # the most-recent RESOLVED period
    recent_met: bool | None  # whether it met


def _guidance_reads(
    rows: Rows, starts: list[int], reference_date: date | None, stale_after_days: int
) -> list[_GuidanceRead]:
    """Per guidance-metric block: the latest guide + the sign-aware delivery record + most-recent
    resolved outcome. Counts ONLY resolved periods (range AND actual); parens are negative; a
    present-but-empty block yields no read. Shared by the string and the table (H4)."""
    reads: list[_GuidanceRead] = []
    for idx, bi in enumerate(starts):
        end = starts[idx + 1] if idx + 1 < len(starts) else len(rows)
        metric = str(rows[bi][0]).strip()
        gdate, guide, actual = _guidance_rows(rows, bi, end)
        header = _nearest_period_header(rows, bi)
        if gdate is None or guide is None or header is None:
            continue
        latest: tuple[date, str, str, bool] | None = None  # date, period, range, cost_like
        recent: tuple[date, str, bool] | None = None  # date, period, met — most-recent resolved
        resolved = met_n = 0
        for j in range(1, len(header)):
            rng = _parse_range(rows[guide][j]) if j < len(rows[guide]) else None
            if rng is None:
                continue
            cost_like = rng[1] < 0  # whole guide range non-positive → a spend/cost guide
            gd = excel_date(rows[gdate][j]) if j < len(rows[gdate]) else None
            per_j = str(header[j]).strip()
            if gd is not None and (latest is None or gd > latest[0]):
                latest = (gd, per_j, str(rows[guide][j]).strip(), cost_like)
            av = _cell_at(rows, actual, j)
            if av is not None:
                resolved += 1
                met = av >= rng[0]  # ≥ floor (revenue) == ≤ ceiling (cost) in signed terms
                met_n += int(met)
                if gd is not None and (recent is None or gd > recent[0]):
                    recent = (gd, per_j, met)
        if latest is None:
            continue
        gd, per, rng_s, cost_like = latest
        pr = _parse_range(rng_s)
        gval = _fig(pr[0]) if (pr is not None and " - " not in rng_s) else f"'{rng_s}'"
        stale = ((reference_date - gd).days if reference_date is not None
                 and (reference_date - gd).days > stale_after_days else None)
        reads.append(_GuidanceRead(
            metric, gval, per, gd, stale, cost_like, resolved, met_n,
            recent[1] if recent is not None else None, recent[2] if recent is not None else None))
    return reads


def guidance_bridge(
    bundle: CiqBundle, *, as_of: str | None = None,
    reference_date: date | None = None, stale_after_days: int = 45,
) -> Sourced[str]:
    """(d) GUIDANCE BRIDGE — per metric: the LATEST guide {range, date} + a delivery track-record.
    SIGN-AWARE: a revenue-like (positive) guide is met when actual ≥ floor; a cost-like (negative)
    guide (e.g. capex) is met when spend ≤ ceiling — the semantic used is labelled. Counts ONLY
    resolved periods (both a range AND an actual) and surfaces the MOST-RECENT resolved outcome
    (MET/MISSED). R3: a guide older than ``stale_after_days`` vs ``reference_date`` is flagged
    '(stale — Nd old)' (age once, no date repeat); a point guide renders numeric, a range verbatim.
    Present-but-empty blocks omitted; parens are negative."""
    try:
        rows = bundle.sheet("estimates", "Guidance")
    except CiqUnavailableError as exc:
        return _miss_or_unknown(bundle, "estimates", exc)
    starts = _metric_starts(rows, _GUIDANCE_METRICS)
    if not starts:
        return Sourced.unknown(note="no guidance metric blocks in Estimates→Guidance")
    lines: list[str] = []
    for r in _guidance_reads(rows, starts, reference_date, stale_after_days):
        seg = f"{r.metric}: latest guide {r.guide} for {r.period} (dated {r.dated.isoformat()})"
        if r.stale_days is not None:
            seg += f" (stale — {r.stale_days}d old)"  # R3: age once, no date repeat
        if r.resolved:
            sem = "spend ≤ guided ceiling" if r.cost_like else "actual ≥ guided floor"
            seg += f"; {sem} {r.met_n}/{r.resolved} resolved"
            if r.recent_period is not None:
                seg += (f"; most recent resolved: {r.recent_period} "
                        f"{'MET' if r.recent_met else 'MISSED'}")
        lines.append(seg)
    if not lines:
        return Sourced.unknown(note="no parseable guidance ranges in Estimates→Guidance")
    return Sourced.present(
        "; ".join(lines) + _asof_suffix(as_of),
        source_ref="CIQ Estimates→Guidance (latest guide + sign-aware delivery track-record)",
    )


def guidance_bridge_rows(
    bundle: CiqBundle, *, reference_date: date | None = None, stale_after_days: int = 45,
) -> Sourced[list[GuidanceRow]]:
    """(H4) The guidance bridge as structured rows for the TABLE — SAME reads as the flat string,
    formatted per column (metric | latest guide | for | dated | age | record | most recent). UNKNOWN
    when the sheet/blocks/ranges are absent (never a fabricated row)."""
    try:
        rows = bundle.sheet("estimates", "Guidance")
    except CiqUnavailableError as exc:
        s: Sourced[str] = _miss_or_unknown(bundle, "estimates", exc)
        return Sourced.unknown(note=s.note or "Estimates→Guidance unavailable")
    starts = _metric_starts(rows, _GUIDANCE_METRICS)
    reads = _guidance_reads(rows, starts, reference_date, stale_after_days) if starts else []
    if not reads:
        return Sourced.unknown(note="no parseable guidance ranges in Estimates→Guidance")
    out: list[GuidanceRow] = []
    for r in reads:
        age = f"{r.stale_days}d (stale)" if r.stale_days is not None else "fresh"
        record = (f"{'spend ≤ ceiling' if r.cost_like else 'actual ≥ floor'} {r.met_n}/{r.resolved}"
                  if r.resolved else "—")
        recent = (f"{r.recent_period} {'MET' if r.recent_met else 'MISSED'}"
                  if r.recent_period is not None else "—")
        out.append(GuidanceRow(
            metric=r.metric, latest_guide=r.guide, period=r.period, dated=r.dated.isoformat(),
            age=age, record=record, most_recent=recent))
    return Sourced.present(
        out, source_ref="CIQ Estimates→Guidance (latest guide + sign-aware delivery track-record)")


def revision_events(bundle: CiqBundle, *, as_of: str | None = None) -> Sourced[list[RevisionEvent]]:
    """(e) REVISION-EVENT LOG — every Estimates→Recent-Changes row as a structured RevisionEvent,
    most-recent-first. The FULL list is kept in JSON; the render caps display at 10. The only
    direction is CIQ's own verbatim ``change_type``; broker/consensus values pass through verbatim
    ("-" preserved), never coerced to a number."""
    try:
        rows = bundle.sheet("estimates", "Recent Changes")
    except CiqUnavailableError as exc:
        return _miss_or_unknown(bundle, "estimates", exc)
    rc = _recent_changes_rows(rows)
    if rc is None:
        return Sourced.unknown(note="no 'Change Type' header in Estimates→Recent Changes")
    out: list[RevisionEvent] = []
    for r in rc[1]:
        c = [str(x).strip() for x in r] + [""] * 10
        d = excel_date(r[1]) if len(r) > 1 else None
        out.append(
            RevisionEvent(
                date=d.isoformat() if d is not None else c[1],
                # R2: an 'Entitlement Needed' broker is a placeholder — group as undisclosed
                change_type=c[0], broker=("broker undisclosed" if _is_entitlement(c[2]) else c[2]),
                metric=c[4], period=c[5],
                broker_prior=c[7], broker_current=c[6],
                consensus_before=c[9], consensus_after=c[8],
            )
        )
    if not out:
        return Sourced.unknown(note="no revision events under the Recent-Changes header")
    out.sort(key=lambda e: e.date, reverse=True)  # ISO dates sort chronologically
    return Sourced.present(
        out,
        source_ref=f"CIQ Estimates→Recent Changes ({len(out)} broker revision events)"
        + _asof_suffix(as_of),
    )


def _rating_distribution(bundle: CiqBundle) -> str | None:
    """Analyst rating counts from Trends 'Non-Periodic Trends' (Buy/Outperform/Hold/…). NOTE: in the
    real CIQ Estimates export the rating rows live in TRENDS, not Consensus as the module contract
    assumed — read here by label (never positionally), Current column."""
    try:
        rows = bundle.sheet("estimates", "Trends")
    except CiqUnavailableError:
        return None
    cats = ("Buy", "Outperform", "Hold", "Underperform", "Sell", "No Opinion")
    out: list[str] = []
    for r in rows:
        base = re.sub(r"\s*\(\d+\)\s*$", "", str(r[0]).strip()) if r else ""
        if base in cats:
            v = clean_num(r[1]) if len(r) > 1 else None
            if v is not None:
                out.append(f"{base} {int(v)}")
    return ", ".join(out) if out else None


def consensus_stats(bundle: CiqBundle, *, as_of: str | None = None) -> Sourced[str]:
    """(f) CONSENSUS STATS — the target-price stats row from Consensus (Mean/Median/High-Low/N) plus
    the analyst rating distribution. CIQ's 'Potential Upside/Downside' is deliberately NOT read: it
    is a conclusion-shaped, stale-target artifact — the human sees price + target and judges."""
    try:
        rows = bundle.sheet("estimates", "Consensus")
    except CiqUnavailableError as exc:
        return _miss_or_unknown(bundle, "estimates", exc)
    parts: list[str] = []
    tp = _find_row_prefix(rows, "Target Price")
    if tp is not None:
        r = rows[tp]
        mean = clean_num(r[1]) if len(r) > 1 else None
        med = clean_num(r[2]) if len(r) > 2 else None
        hilo = str(r[3]).strip() if len(r) > 3 else ""
        n = str(r[5]).strip() if len(r) > 5 else ""
        seg: list[str] = []
        if mean is not None:
            seg.append(f"mean {_usd(mean)}")
        if med is not None:
            seg.append(f"median {_usd(med)}")
        if hilo and hilo not in _UNAVAILABLE_CELLS:
            seg.append(f"high/low {hilo}")
        if n and n not in _UNAVAILABLE_CELLS:
            seg.append(f"N {n}")
        if seg:
            parts.append("Target price: " + ", ".join(seg))
    ratings = _rating_distribution(bundle)
    if ratings:
        parts.append("Ratings: " + ratings)
    if not parts:
        return Sourced.unknown(note="no Target Price / rating rows in Estimates→Consensus/Trends")
    return Sourced.present(
        "; ".join(parts) + _asof_suffix(as_of),
        source_ref="CIQ Estimates→Consensus (target stats) + Trends Non-Periodic (ratings)",
    )


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


# the synthesis LLM gets a MECHANICALLY-bounded slice (sections + a fixed char budget) — a
# structural cut, never a topic/relevance selection. The DOSSIER embeds nothing (a pointer only).
_SYNTHESIS_TRANSCRIPT_BUDGET = 12_000


def transcript_for_synthesis(bundle: CiqBundle) -> str | None:
    """Mechanically-bounded transcript slices for the synthesis LLM INPUT ONLY (never embedded in
    the dossier): boilerplate stripped (operator intro / forward-looking legalese / estimates / TOC,
    via ``_transcript_prose``), prepared remarks + Q&A. ALL earnings-call transcripts on file are
    included (so quarter-over-quarter posture is visible), each LABELLED by call and capped to the
    FULL char budget independently — so adding the prior quarter never truncates the latest call's
    Q&A (the prompt scales with the ~2 quarters the operator uploads, not a halved split). A
    structural cut, NOT a topic selection. None when there's no transcript or none parse."""
    wbs = bundle.all_workbooks("transcript")
    if not wbs:
        return None
    slices: list[str] = []
    for wb in wbs:
        try:
            prose = _transcript_prose(read_text(wb.path, wb.fmt))[:_SYNTHESIS_TRANSCRIPT_BUDGET]
        except CiqParseError:
            continue
        if prose.strip():
            slices.append(f"--- {wb.path.name} ---\n{prose}")
    return "\n\n".join(slices) if slices else None


def management_commentary(bundle: CiqBundle) -> Sourced[str]:
    """A POINTER to the earnings-call transcript(s) — NOT an embedded/machine-selected excerpt. The
    human reads them in full for management posture/tone; the machine points, it does not curate
    transcript content (a machine-chosen 'salient extract' is the relevance judgment this project
    forbids; the full embed is a duplicate that bloated the synthesis prompt). All calls on file are
    fed to the synthesis LLM (which cites them where a point rests on posture); this is the human's
    full-read pointer to them."""
    wbs = bundle.all_workbooks("transcript")
    if not wbs:
        return Sourced.missing(note=f"no earnings-call transcript for {bundle.ticker} — pull it")
    names = "; ".join(wb.path.name for wb in wbs)
    return Sourced.present(
        f"{len(wbs)} earnings-call transcript(s) on file — read in full for management posture: "
        f"{names} (pointer only; the synthesis cites them, the machine does not curate an excerpt)",
        source_ref=f"CIQ transcript(s): {names}",
    )


# --- peer comps (CIQ Company Comparable Analysis) — FRAMED to resist the consensus comp read ------

_COMPS_MULTIPLES = (  # Trading Multiples: (label, col). LTM + NTM forward.
    ("TEV/Rev", 1), ("TEV/EBITDA", 2), ("P/E", 4),
    ("NTM TEV/Rev", 6), ("NTM TEV/EBITDA", 7), ("NTM P/E", 8),
)
_COMPS_DELTAS = (  # Operating Statistics: (label, col, is_pct) — the earned-vs-residual inputs.
    ("EBITDA margin", 2, True), ("rev growth", 5, True), ("EBITDA growth", 6, True),
    ("Debt/EBITDA", 10, False), ("LT EPS growth", 11, True), ("beta", 12, False),
)


def _comps_short_name(full: str) -> str:
    """'Roku, Inc. (NasdaqGS:ROKU)' → 'Roku'."""
    return re.split(r",| \(", full.strip(), maxsplit=1)[0].strip() or full.strip()


def _row_ticker(cell: Any) -> str | None:
    """The exchange-qualified symbol from a comps company cell → its bare ticker, upper-cased:
    'Microvast Holdings, Inc. (NasdaqCM:MVST)' → 'MVST', 'Samsung SDI Co., Ltd. (KOSE:A006400)' →
    'A006400'. None when no '(EXCHANGE:SYMBOL)' paren is present (e.g. a private/defunct peer)."""
    for grp in re.findall(r"\(([^)]*)\)", str(cell)):
        if ":" in grp:
            return grp.split(":")[-1].strip().upper() or None
    return None


def _comps_cell(rows: Rows, ri: int | None, ci: int) -> float | str | None:
    """A comps cell → rounded number, the literal 'NM' (a REAL not-meaningful state — a negative/
    near-zero base, never dropped), or None for true-blank/'-'. clean_num would lump NM into
    UNAVAILABLE; here NM is informative (it signals peer-set heterogeneity)."""
    if ri is None or ri >= len(rows) or ci >= len(rows[ri]):
        return None
    if str(rows[ri][ci]).strip().upper() == "NM":
        return "NM"
    return clean_num(rows[ri][ci])


def _comps_layout(rows: Rows, ticker: str) -> tuple[int | None, list[int], int | None]:
    """(header_i, peer_indices, target_i) for a Comparable-Analysis sheet. The SUBJECT (target) is
    identified by matching ``ticker`` against the '(EXCHANGE:SYMBOL)' paren in col 0 — authoritative
    because CIQ interleaves the subject among the peers and separates it only by convention. The old
    'first company row after a positional gap' heuristic mis-fired whenever a no-ticker peer (e.g. a
    private/defunct comparable) broke the contiguous block — MVST resolved to Samsung SDI, not
    Microvast. Fallback when the ticker isn't found: the LAST company row before 'Summary Stats'
    (CIQ places the subject last). Peers = the other ticker-bearing rows. A company row must
    carry an '(EXCHANGE:SYMBOL)' ticker in col 0 — a BARE paren is NOT enough: sheets without a
    'Summary Statistics' delimiter (Credit Health, Implied Valuation, Business Description) set
    ``end = len(rows)`` and would otherwise pull a trailing prose row (the S&P disclaimer 'No
    content (including ratings…') into the peer set — and via the ``company[-1]`` fallback even make
    it the subject. Requiring a real ticker excludes such rows (verified on MVST: drops only the
    disclaimer, no real peer, on every comps sheet)."""
    hdr = _find_row(rows, "Company Name")
    if hdr is None:
        return None, [], None
    end = _find_row(rows, "Summary Statistics") or len(rows)
    company = [i for i in range(hdr + 1, end) if rows[i] and _row_ticker(rows[i][0]) is not None]
    if not company:
        return hdr, [], None
    want = (ticker or "").strip().upper()
    target = next((i for i in company if _row_ticker(rows[i][0]) == want), None)
    if target is None:
        target = company[-1]
    peers = [i for i in company if i != target]
    return hdr, peers, target


def _tok(v: float | str | None) -> str:
    """A multiple/stat display token: 'NM', a compact number, or an em-dash."""
    if v == "NM":
        return "NM"
    return f"{v:g}" if isinstance(v, (int, float)) else "–"


def _fmt_cap(m: float | None) -> str:
    if m is None:
        return "?"
    return f"${m / 1000:.1f}B" if m >= 1000 else f"${m:.0f}M"


def _comps_multiples(bundle: CiqBundle, src: str) -> Sourced[str]:
    try:
        tm = bundle.sheet("comps", "Trading Multiples")
    except CiqUnavailableError as exc:
        return _miss_or_unknown(bundle, "comps", exc)
    _hdr, _peers, tgt = _comps_layout(tm, bundle.ticker)
    stat_row = {k: _find_row(tm, k) for k in ("Low", "Median", "Mean", "High")}
    if tgt is None and not any(stat_row.values()):
        return Sourced.unknown(note="Trading Multiples: no target row / summary block")
    bits: list[str] = []
    for lab, col in _COMPS_MULTIPLES:
        peer_stats = " / ".join(
            f"{k} {_tok(_comps_cell(tm, stat_row[k], col))}"
            for k in ("Low", "Median", "Mean", "High") if stat_row[k] is not None
        )
        bits.append(f"{lab}: name {_tok(_comps_cell(tm, tgt, col))} vs peers {peer_stats}")
    return Sourced.present(
        "; ".join(bits) + "  [NM = a real state (negative base), not missing]",
        source_ref=f"{src}→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)",
    )


def _comps_deltas(bundle: CiqBundle, src: str) -> Sourced[str]:
    try:
        op = bundle.sheet("comps", "Operating Statistics")
    except CiqUnavailableError as exc:
        return _miss_or_unknown(bundle, "comps", exc)
    _hdr, peers, tgt = _comps_layout(op, bundle.ticker)
    if tgt is None:
        return Sourced.unknown(note="Operating Statistics: no target row")
    bits: list[str] = []
    for lab, col, pct in _COMPS_DELTAS:
        nv = _comps_cell(op, tgt, col)
        peer_vals = [v for i in peers if isinstance((v := _comps_cell(op, i, col)), (int, float))]
        med = statistics.median(peer_vals) if peer_vals else None

        def _f(x: float, p: bool = pct) -> str:
            return f"{x * 100:.0f}%" if p else f"{x:.1f}"

        ns = _f(nv) if isinstance(nv, (int, float)) else _tok(nv)
        ms = _f(med) if med is not None else "–"
        bits.append(f"{lab} name {ns} vs peer-median {ms}")
    return Sourced.present(
        "; ".join(bits) + "  [justified-vs-residual inputs: is the discount EARNED (worse "
        "fundamentals) or RESIDUAL (unexplained)? the human judges — not computed here]",
        source_ref=f"{src}→Operating Statistics (name vs peer median: growth/margin/leverage/beta)",
    )


def cross_sectional_valuation(bundle: CiqBundle) -> Sourced[str]:
    """The CROSS-SECTIONAL read — the fund's edge: where the name's multiples sit vs the PEER
    cross-section (not its own history). Name EV/EBITDA & P/E vs the peer MEDIAN, NUMBERS ONLY — the
    earned-vs-residual framing and peer comparability live in the Peer-comps section (where the
    inputs are), so a fixed 'is the discount earned or residual?' tail here would be identical on
    every dossier and add no per-name value. A raw discount is not a verdict; the synthesis
    PEER-COMP-BARE guardrail resists reading it as one. Reads the Comparable-Analysis sheet."""
    try:
        tm = bundle.sheet("comps", "Trading Multiples")
    except CiqUnavailableError as exc:
        return _miss_or_unknown(bundle, "comps", exc)
    _hdr, _peers, tgt = _comps_layout(tm, bundle.ticker)
    med = _find_row(tm, "Median")
    if tgt is None or med is None:
        return Sourced.unknown(note="Trading Multiples: no target row / Median statistic")
    bits: list[str] = []
    for lab, col in (("EV/EBITDA", 2), ("P/E", 4)):
        nv, mv = _comps_cell(tm, tgt, col), _comps_cell(tm, med, col)
        if isinstance(nv, (int, float)) and isinstance(mv, (int, float)) and mv:
            bits.append(f"{lab} {nv:g}x vs peer median {mv:g}x ({nv / mv - 1:+.0%})")
        else:
            bits.append(f"{lab} {_tok(nv)} vs peer median {_tok(mv)}")
    return Sourced.present(
        "; ".join(bits),
        source_ref="CIQ Comparable Analysis→Trading Multiples (name vs peer Median)",
    )


def comps_ev_ebitda(bundle: CiqBundle) -> Sourced[float]:
    """The name's LTM TEV/EBITDA from the Comparable-Analysis Trading-Multiples sheet, as a VALUE so
    it can be reconciled against the Financials→Multiples TEV/LTM (``ev_ebitda_current``). The two
    are the same concept computed by different CIQ sheets and can disagree by EBITDA/EV basis (the
    MVST 10.0x vs 38.4x case)."""
    try:
        tm = bundle.sheet("comps", "Trading Multiples")
    except CiqUnavailableError as exc:
        return _miss_or_unknown(bundle, "comps", exc)
    _hdr, _peers, tgt = _comps_layout(tm, bundle.ticker)
    if tgt is None:
        return Sourced.unknown(note="Trading Multiples: no target (name) row")
    v = _comps_cell(tm, tgt, 2)  # col 2 = TEV/EBITDA (LTM)
    if not isinstance(v, (int, float)):
        return Sourced.unknown(note=f"Trading Multiples TEV/EBITDA not numeric ({_tok(v)})")
    return Sourced.present(
        round(float(v), 1),
        source_ref="CIQ Comparable Analysis→Trading Multiples (name row, TEV/EBITDA LTM)",
    )


def peer_comps(bundle: CiqBundle) -> PeerComps:
    """Assemble the peer-comps section from the CIQ Company Comparable Analysis workbook: roster +
    market-cap/business dispersion + the name-vs-peer multiple gap (LTM + NTM) + the fundamental
    deltas — each fail-loud UNKNOWN/MISSING if its sheet is absent. NM preserved (a real state);
    the Implied Valuation sheet is deliberately SKIPPED (the consensus implied-upside trap)."""
    src = "CIQ Comparable Analysis"
    caps: dict[str, float] = {}
    peer_caps: list[float] = []
    name_cap: float | None = None
    try:
        fd = bundle.sheet("comps", "Financial Data")
        _hdr, peers, tgt = _comps_layout(fd, bundle.ticker)
        for i in peers:
            nm = _comps_short_name(str(fd[i][0]))
            c = clean_num(fd[i][3]) if len(fd[i]) > 3 else None
            if c is not None:
                caps[nm] = c
                peer_caps.append(c)
        if tgt is not None and len(fd[tgt]) > 3:
            name_cap = clean_num(fd[tgt][3])
    except CiqUnavailableError:
        pass
    desc: dict[str, str] = {}
    try:
        bd = bundle.sheet("comps", "Business Description")
        _hdr, bpeers, _t = _comps_layout(bd, bundle.ticker)
        for i in bpeers:
            nm = _comps_short_name(str(bd[i][0]))
            full = str(bd[i][1]).strip() if len(bd[i]) > 1 else ""
            vm = re.search(
                r"\b(operates|provides|engages|develops|offers|designs|manufactures|owns|"
                r"distributes|focuses|is a)\b", full,
            )
            d = (full[vm.start():] if vm else full)[:55].rsplit(" ", 1)[0]
            hq = str(bd[i][2]).strip().rsplit(",", 1)[-1].strip()[:18] if len(bd[i]) > 2 else ""
            desc[nm] = f"{d} ({hq})" if hq else d
    except CiqUnavailableError:
        pass

    if caps:
        roster = "; ".join(
            f"{nm} {_fmt_cap(caps[nm])}" + (f" — {desc[nm]}" if desc.get(nm) else "") for nm in caps
        )
        tail = f" | the name: {_fmt_cap(name_cap)}" if name_cap is not None else ""
        peer_set = Sourced.present(
            f"{len(caps)} peers — {roster}{tail}",
            source_ref=f"{src}→Financial Data + Business Description (roster + caps + business)",
        )
    else:
        peer_set = _miss_or_unknown(bundle, "comps", CiqUnavailableError("Financial Data roster"))

    if peer_caps:
        hi, lo = max(peer_caps), min(peer_caps)
        spread = hi / lo if lo else 0.0
        het = "HETEROGENEOUS — low comparability" if spread >= 10 else "moderately dispersed"
        gate = f"market caps span {_fmt_cap(lo)}–{_fmt_cap(hi)} ({spread:.0f}x)"
        gate += f"; the name is {_fmt_cap(name_cap)}" if name_cap is not None else ""
        comparability = Sourced.present(
            f"{gate} → {het}: the peer median is anchored by businesses of differing scale/model; "
            "scrutinise comparability before reading any peer stat as a clean benchmark.",
            source_ref=f"{src}→Financial Data (market-cap dispersion) + Business Description",
        )
    else:
        comparability = _miss_or_unknown(bundle, "comps", CiqUnavailableError("market caps"))

    return PeerComps(
        peer_set=peer_set,
        comparability=comparability,
        trading_multiples=_comps_multiples(bundle, src),
        fundamental_deltas=_comps_deltas(bundle, src),
        peer_grid=peer_grid(bundle),
    )


# --- PR B: as-of sidecar (R1), per-peer grid (B1), credit health + total-debt basis (B2),
# --- implied valuation (B3). The comps workbook HAS an explicit As-Of header (unlike Estimates).


def _is_entitlement(cell: Any) -> bool:
    """R2: a CIQ 'Entitlement Needed' cell — a placeholder, not data (case-insensitive)."""
    return str(cell).strip().lower() == "entitlement needed"


def _undisclosed_name(name: str) -> str:
    """R2: an 'Entitlement Needed' company/broker name → 'undisclosed (CIQ entitlement)'."""
    return "undisclosed (CIQ entitlement)" if _is_entitlement(name) else name


def _sidecar_as_of(bundle: CiqBundle) -> date | None:
    """The operator-attested export date from an optional ``data/manual/ciq/<TICKER>/AS_OF`` file
    (YYYY-MM-DD), derived from a workbook's folder — no loader change. None if absent/malformed."""
    for wb in bundle.workbooks:
        p = wb.path.parent / "AS_OF"
        try:
            if p.exists():
                return date.fromisoformat(p.read_text().strip()[:10])
        except (ValueError, OSError):
            return None
    return None


def comps_as_of(bundle: CiqBundle) -> Sourced[str]:
    """The comps workbook's as-of — an EXPLICIT 'As-Of Date:' header (present on every sheet; MVST
    decodes to 2026-06-24), else the operator AS_OF sidecar (attested), else UNKNOWN. Header present
    → plain as-of (the A.1 discipline)."""
    try:
        rows = bundle.sheet("comps", "Financial Data")
    except CiqUnavailableError as exc:
        return _miss_or_unknown(bundle, "comps", exc)
    d = _scan_asof_header(rows)
    if d is not None:
        return Sourced.present(
            d.isoformat(), source_ref="CIQ Comparable Analysis 'As-Of Date' header (workbook as-of)"
        )
    sc = _sidecar_as_of(bundle)
    if sc is not None:
        return Sourced.present(
            sc.isoformat(), source_ref="operator AS_OF sidecar", note="operator-attested"
        )
    return Sourced.unknown(note="no As-Of header or AS_OF sidecar for the comps workbook")


def _comps_asof_suffix(bundle: CiqBundle) -> str:
    """' · as-of YYYY-MM-DD' stamped on every comps source_ref (with '· operator-attested' when the
    date came from the sidecar). '' when neither header nor sidecar is present."""
    a = comps_as_of(bundle)
    if a.status is not SourceStatus.PRESENT or not a.value:
        return ""
    att = " · operator-attested" if (a.note and "operator-attested" in a.note) else ""
    return f" · as-of {a.value}{att}"


def _num_or_none(v: float | str | None) -> float | None:
    return v if isinstance(v, (int, float)) else None


def peer_grid(bundle: CiqBundle) -> Sourced[list[PeerRow]]:
    """(B1) Per-peer comparability grid: one row per peer + the subject + a peer-median footer, from
    Financial Data (cap, net debt) JOINED to Operating Statistics (margins/growth/Debt-EBITDA) BY
    TICKER (row order differs per sheet). Sorted by market cap desc. No computed delta — the human
    compares the name row against the peers + the median footer."""
    try:
        fd = bundle.sheet("comps", "Financial Data")
        op = bundle.sheet("comps", "Operating Statistics")
    except CiqUnavailableError as exc:
        return _miss_or_unknown(bundle, "comps", exc)
    fh, fpeers, ftgt = _comps_layout(fd, bundle.ticker)
    _oh, opeers, otgt = _comps_layout(op, bundle.ticker)
    if fh is None or not fpeers:
        return Sourced.unknown(note="Financial Data: no Company Name header / peer rows")
    op_by_tkr: dict[str, int] = {}
    for i in ([otgt] if otgt is not None else []) + opeers:
        if (t := _row_ticker(op[i][0])):
            op_by_tkr[t] = i

    def row_for(fi: int, is_name: bool) -> PeerRow:
        tkr = _row_ticker(fd[fi][0]) or ""
        oi = op_by_tkr.get(tkr)
        de = _comps_cell(op, oi, 10) if oi is not None else None
        return PeerRow(
            name=_undisclosed_name(_comps_short_name(str(fd[fi][0]))), ticker=tkr, is_name=is_name,
            market_cap=_num_or_none(_comps_cell(fd, fi, 3)),
            net_debt=_num_or_none(_comps_cell(fd, fi, 4)),
            ebitda_margin=_num_or_none(_comps_cell(op, oi, 2)) if oi is not None else None,
            rev_growth_1y=_num_or_none(_comps_cell(op, oi, 5)) if oi is not None else None,
            ebitda_growth_1y=_num_or_none(_comps_cell(op, oi, 6)) if oi is not None else None,
            debt_to_ebitda=(_tok(de) if de is not None else None),
        )

    peers = [row_for(i, False) for i in fpeers]
    rows: list[PeerRow] = list(peers)
    if ftgt is not None:
        rows.append(row_for(ftgt, True))
    rows.sort(key=lambda r: (r.market_cap is None, -(r.market_cap or 0.0)))

    def _med(vals: list[float | None]) -> float | None:
        xs = [v for v in vals if v is not None]
        return statistics.median(xs) if xs else None

    de_nums = [v for i in opeers if isinstance((v := _comps_cell(op, i, 10)), (int, float))]
    med_de = statistics.median(de_nums) if de_nums else None
    rows.append(PeerRow(
        name="Peer median", ticker="", is_median=True,
        market_cap=_med([p.market_cap for p in peers]),
        net_debt=_med([p.net_debt for p in peers]),
        ebitda_margin=_med([p.ebitda_margin for p in peers]),
        rev_growth_1y=_med([p.rev_growth_1y for p in peers]),
        ebitda_growth_1y=_med([p.ebitda_growth_1y for p in peers]),
        debt_to_ebitda=(f"{med_de:.1f}" if med_de is not None else None),
    ))
    return Sourced.present(
        rows,
        source_ref="CIQ Comparable Analysis→Financial Data + Operating Statistics (per-peer grid)"
        + _comps_asof_suffix(bundle),
    )


def _issuer_rating(cell: Any) -> str:
    """The S&P issuer rating cell → verbatim rating or '' when absent ('-'/blank/Entitlement)."""
    s = str(cell).strip()
    return "" if s in _UNAVAILABLE_CELLS or s.lower() == "entitlement needed" else s


def _is_investment_grade(rating: str) -> bool | None:
    """An S&P long-term issuer rating → True (investment-grade, BBB- and up), False (sub-IG / high
    yield, BB+ and down), or None when not a parseable letter grade. Used to verify the credit-scale
    direction WITHIN the rated set (IG should score stronger) — robust on a quality roster where an
    'unrated' peer does NOT imply weak."""
    m = re.match(r"[A-Da-d]+", rating.strip())
    if not m:
        return None
    letters = m.group(0).upper()
    if letters in {"AAA", "AA", "A", "BBB"}:
        return True
    if letters in {"BB", "B", "CCC", "CC", "C", "D"}:
        return False
    return None


def credit_health(bundle: CiqBundle) -> Sourced[str]:
    """(B2 leg) S&P-MI credit-health scores — name vs peers, scale LABELED. Scale direction is
    verified FROM THE DATA, TIERED (1=strongest…4=weakest): (1) within the rated set, IG peers score
    ≤ sub-IG peers (robust on a quality roster where 'unrated' ≠ weak); (2) fallback rated-score <
    unrated-score; (3) else UNKNOWN — never a guessed direction."""
    try:
        ch = bundle.sheet("comps", "Credit Health Panel")
    except CiqUnavailableError as exc:
        return _miss_or_unknown(bundle, "comps", exc)
    _h, peers, tgt = _comps_layout(ch, bundle.ticker)
    if tgt is None:
        return Sourced.unknown(note="Credit Health Panel: no name row")

    def overall(i: int) -> float | None:
        return _num_or_none(_comps_cell(ch, i, 1))

    # Peer Overall scores paired with issuer rating (verbatim; '' = unrated).
    scored = [(_issuer_rating(ch[i][7]), o) for i in peers if (o := overall(i)) is not None]
    ig = [o for r, o in scored if _is_investment_grade(r) is True]
    sub_ig = [o for r, o in scored if _is_investment_grade(r) is False]
    rated = [o for r, o in scored if r]
    unrated = [o for r, o in scored if not r]
    # TIERED scale-direction verification — a quality roster's 'unrated' peers are NOT weak, so the
    # rated-vs-unrated split can read falsely ambiguous; verify WITHIN the rated set first.
    direction_ok = (
        (len(ig) >= 1 and len(sub_ig) >= 1 and statistics.mean(ig) <= statistics.mean(sub_ig))
        or (bool(rated) and bool(unrated) and statistics.mean(rated) < statistics.mean(unrated))
    )
    if not direction_ok:
        return Sourced.unknown(note="Credit Health Panel: scale direction ambiguous — not rendered")
    scores = "/".join(_tok(_comps_cell(ch, tgt, c)) for c in (1, 2, 3, 4))
    name_rating = _issuer_rating(ch[tgt][7]) or "unrated"

    def dim_median(c: int) -> str:  # R1: peer median per dimension (not Overall only)
        vals = [v for i in peers if isinstance((v := _comps_cell(ch, i, c)), (int, float))]
        return f"{statistics.median(vals):g}" if vals else "–"

    peer_med = "/".join(dim_median(c) for c in (1, 2, 3, 4))
    return Sourced.present(
        f"name Overall/Operational/Solvency/Liquidity {scores} (S&P issuer rating {name_rating}); "
        f"peer-median O/Op/S/L {peer_med}; scale 1=strongest … 4=weakest (S&P-MI PD model)",
        source_ref="CIQ Comparable Analysis→Credit Health Panel" + _comps_asof_suffix(bundle),
    )


def comps_total_debt_ebitda(bundle: CiqBundle) -> Sourced[str]:
    """(B2 leg) Name TOTAL-debt/EBITDA vs peer median, comps basis (Operating Statistics col).
    LABELED total-debt basis — distinct from the CIQ NET-debt/EBITDA (Financials), NEVER mixed."""
    try:
        op = bundle.sheet("comps", "Operating Statistics")
    except CiqUnavailableError as exc:
        return _miss_or_unknown(bundle, "comps", exc)
    _h, peers, tgt = _comps_layout(op, bundle.ticker)
    if tgt is None:
        return Sourced.unknown(note="Operating Statistics: no name row")
    nv = _comps_cell(op, tgt, 10)
    peer_vals = [v for i in peers if isinstance((v := _comps_cell(op, i, 10)), (int, float))]
    med = statistics.median(peer_vals) if peer_vals else None
    ns = f"{nv:.1f}x" if isinstance(nv, (int, float)) else _tok(nv)
    ms = f"{med:.1f}x" if med is not None else "–"
    return Sourced.present(
        f"name {ns} vs peer median {ms} (comps TOTAL-debt/EBITDA basis)",
        source_ref="CIQ Comparable Analysis→Operating Statistics (LTM Total Debt/EBITDA)"
        + _comps_asof_suffix(bundle),
    )


def _iv_stat_rows(rows: Rows, start: int, end: int) -> dict[str, int | None]:
    """The {High,Low,Mean,Median} row indices inside an Implied-Valuation section [start, end)."""
    return {
        k: next((i for i in range(start, end) if rows[i] and str(rows[i][0]).strip() == k), None)
        for k in ("High", "Low", "Mean", "Median")
    }


def implied_valuation(bundle: CiqBundle, comparability_gate: Sourced[str]) -> ImpliedValuation:
    """(B3) CIQ's Implied-Valuation sheet: the implied EQUITY value at peer multiples (basis ×
    Low/Median/Mean/High) + the TEV→equity bridge + the name's ACTUAL market cap ADJACENT. POSED,
    never concluded — no computed %/discount/upside. The heterogeneity gate is on its header."""
    try:
        iv = bundle.sheet("comps", "Implied Valuation")
    except CiqUnavailableError as exc:
        m: Sourced[Any] = _miss_or_unknown(bundle, "comps", exc)
        return ImpliedValuation(
            implied_equity=m, bridge=m, market_cap=m, comparability_gate=comparability_gate
        )
    suffix = _comps_asof_suffix(bundle)
    hdr = _find_row(iv, "Company Name")
    eq_hdr = _find_row(iv, "= Implied Equity Value")
    shares_hdr = _find_row(iv, "/ Shares Outstanding")
    if hdr is None or eq_hdr is None:
        unk: Sourced[Any] = Sourced.unknown(note="Implied Valuation: no header / equity section")
        return ImpliedValuation(
            implied_equity=unk, bridge=unk, market_cap=comps_market_cap(bundle),
            comparability_gate=comparability_gate,
        )
    bases = [str(c).strip() for c in iv[hdr][1:]]
    stat = _iv_stat_rows(iv, eq_hdr, shares_hdr or len(iv))
    eq_rows: list[ImpliedRow] = []
    for j, basis in enumerate(bases, start=1):
        if not basis:
            continue
        vals = {k: (_num_or_none(_comps_cell(iv, ri, j))) for k, ri in stat.items()}
        if any(v is not None for v in vals.values()):
            eq_rows.append(ImpliedRow(
                basis=basis, low=vals["Low"], median=vals["Median"],
                mean=vals["Mean"], high=vals["High"],
            ))
    equity = (
        Sourced.present(eq_rows, source_ref="CIQ Comparable Analysis→Implied Valuation "
                        "(= Implied Equity Value, basis × Low/Median/Mean/High)" + suffix)
        if eq_rows else Sourced.unknown(note="Implied Valuation: no implied-equity rows")
    )
    cash_i, debt_i = _find_row(iv, "+ Total Cash & ST Investments"), _find_row(iv, "- Total Debt")
    cash = _num_or_none(_comps_cell(iv, cash_i, 1)) if cash_i is not None else None
    debt = _num_or_none(_comps_cell(iv, debt_i, 1)) if debt_i is not None else None
    bridge: Sourced[str] = (
        Sourced.present(
            f"TEV→equity bridge: + cash {_usd(cash)}M, − total debt {_usd(debt)}M",
            source_ref="CIQ Comparable Analysis→Implied Valuation (cash/debt bridge)" + suffix,
        )
        if cash is not None or debt is not None
        else Sourced.unknown(note="Implied Valuation: no cash/debt bridge rows")
    )
    return ImpliedValuation(
        implied_equity=equity, bridge=bridge, bridge_cash=cash, bridge_debt=debt,
        market_cap=comps_market_cap(bundle), comparability_gate=comparability_gate,
    )


def comps_market_cap(bundle: CiqBundle) -> Sourced[float]:
    """The name's ACTUAL market cap ($M) from Financial Data — the adjacent fact the human sets the
    CIQ-implied equity values against (no computed discount)."""
    try:
        fd = bundle.sheet("comps", "Financial Data")
    except CiqUnavailableError as exc:
        return _miss_or_unknown(bundle, "comps", exc)
    _h, _p, tgt = _comps_layout(fd, bundle.ticker)
    mc = _num_or_none(_comps_cell(fd, tgt, 3)) if tgt is not None else None
    if mc is None:
        return Sourced.unknown(note="Financial Data: no market cap for the name")
    return Sourced.present(
        round(mc, 1),
        source_ref="CIQ Comparable Analysis→Financial Data (name Market Capitalization Latest)"
        + _comps_asof_suffix(bundle),
    )


# --- PR C: the FINANCIAL-SUMMARY appendix (C1 annual+estimates, C2 8-quarter, C3 balance-sheet).
# Reuses the financials period/reclassified helpers; estimate columns come from Estimates→Trends
# "Current" per FY; growth is NEVER computed across a basis change (renders "— (basis)").


def _fin_short(cell: Any) -> str:
    """A Financials period-header cell → a compact label: '12 months Dec-31-2022' → 'FY22';
    '3 months Q1 Mar-31-2026' → 'Q1-26'; 'LTM …' → 'LTM'; a bare serial (Balance Sheet 'as of')
    → 'FY25' (Dec) or 'Mar-26' (interim)."""
    c = str(cell).replace("\n", " ").strip()
    if "LTM" in c.upper():
        return "LTM"
    qm = re.search(r"\bQ(\d)\b", c)
    ym = re.search(r"(\d{4})", c)
    if "months" in c.lower() or qm:
        yy = ym.group(1)[2:] if ym else "?"
        return f"Q{qm.group(1)}-{yy}" if qm else f"FY{yy}"
    d = excel_date(cell)
    if d is not None:
        return f"FY{d.year % 100:02d}" if d.month == 12 else f"{d:%b-%y}"
    return f"FY{ym.group(1)[2:]}" if ym else (c[:8] or "?")


def _fin_periods(hdr: list[Any]) -> list[tuple[int, str, bool, bool]]:
    """(col, short_label, is_ltm, is_reclassified) for each non-empty period column of a header."""
    return [
        (j, _fin_short(hdr[j]), _is_ltm(hdr[j]), "Reclassified" in str(hdr[j]))
        for j in range(1, len(hdr))
        if str(hdr[j]).strip()
    ]


def _est_fy_current(rows: Rows | None, metric: str, fy_label: str) -> float | None:
    """The Estimates→Trends 'Current' consensus for ``metric`` at the ``fy_label`` (e.g. 'FY 2026')
    column — the FY-level E figure. None when the metric/period/Current row is absent."""
    if rows is None:
        return None
    bi = _find_row(rows, metric)
    header = _metric_block_header(rows, bi) if bi is not None else None
    if bi is None or header is None:
        return None
    col = next((j for j, c in enumerate(header) if str(c).strip() == fy_label), None)
    cur = next(
        (rows[k] for k in range(bi + 1, min(bi + 9, len(rows)))
         if str(rows[k][0]).strip() == "Current"),
        None,
    )
    return clean_num(cur[col]) if cur is not None and col is not None and col < len(cur) else None


def _fmt_m(v: float | None) -> str:  # $M figure → "444" / "-13" / "—"
    return f"{v:,.0f}" if v is not None else "—"


def _fmt_eps(v: float | None) -> str:  # per-share → "0.04" / "—"
    return f"{v:.2f}" if v is not None else "—"


_C1_ROWS: tuple[tuple[str, str, str, str], ...] = (  # (display, IS label, Estimates metric, fmt)
    ("Revenue", "Total Revenue", "Revenue", "m"),
    ("EBITDA", "EBITDA", "EBITDA", "m"),
    ("EBIT", "EBIT", "EBIT", "m"),
    ("Net income", "Net Income", "Net Income (GAAP)", "m"),
    # (D5a) EPS split — SAME-BASIS in every column: the GAAP row (actual 'Diluted EPS' + Trends
    # 'EPS (GAAP)') pairs with GAAP Net income; the Normalized row uses 'Normalized Diluted EPS' +
    # 'EPS Normalized'. Each series reads its OWN basis, so a basis absent from Trends renders "—"
    # (via _fmt_eps(None)) and NEVER borrows the other.
    ("EPS (GAAP, dil.)", "Diluted EPS", "EPS (GAAP)", "e"),
    ("EPS (Normalized)", "Normalized Diluted EPS", "EPS Normalized", "e"),
)
_C1_CF: tuple[tuple[str, str], ...] = (
    ("CFO", "Cash from Ops."), ("Capex", "Capital Expenditure"), ("FCF", "Levered Free Cash Flow"),
)


def financial_summary_annual(bundle: CiqBundle, *, as_of: str | None = None) -> Sourced[FinTable]:
    """(C1 + C4) Annual actuals (last-4-FY + LTM, from Financials Income Statement + Cash Flow)
    fused with FY2026E/FY2027E consensus (Estimates→Trends 'Current'). E cols marked; growth is
    never computed across a Reclassified basis ('— (basis)'), and an FY estimate's growth is vs the
    PRIOR FISCAL YEAR ('+4% (vs FY25)'), not the overlapping LTM (D5c). EPS is split into same-basis
    GAAP + Normalized rows (D5a). Core rows fail loud; supplementary rows render only if present."""
    try:
        inc = bundle.sheet("financials", "Income Statement", freq="annual")
    except CiqUnavailableError as exc:
        return _miss_or_unknown(bundle, "financials", exc)
    hdr = _period_header(inc)
    if hdr is None:
        return Sourced.unknown(note="Income Statement (annual): no Fiscal Period header")
    periods = _fin_periods(inc[hdr])
    fy = [p for p in periods if not p[2]]
    ltm = [p for p in periods if p[2]]
    disp = fy[-4:] + ltm[:1]
    if not disp:
        return Sourced.unknown(note="Income Statement (annual): no period columns")
    act_cols = [c for c, _s, _l, _r in disp]
    # LTM is its own basis (a ttm, not a fiscal year), so growth never spans the FY↔LTM boundary
    # (overlapping, non-successor) — it reads "— (basis)"; the estimate boundary names its base.
    bases = [("ltm" if lt else ("recl" if r else "act")) for _c, _s, lt, r in disp] + ["est", "est"]
    columns = [s + (" (R)" if r else "") for _c, s, _l, r in disp] + ["FY26E", "FY27E"]
    est_fys = ("FY 2026", "FY 2027")
    try:
        tr: Rows | None = bundle.sheet("estimates", "Trends")
    except CiqUnavailableError:
        tr = None

    def series(is_label: str, est_metric: str | None) -> list[float | None]:
        ri = _find_row(inc, is_label)
        act = [
            clean_num(inc[ri][c]) if ri is not None and c < len(inc[ri]) else None for c in act_cols
        ]
        est = (
            [_est_fy_current(tr, est_metric, fy) for fy in est_fys] if est_metric else [None, None]
        )
        return act + est

    fy_cols = [i for i, bb in enumerate(bases) if bb in ("act", "recl")]
    prior_fy = fy_cols[-1] if fy_cols else None  # (D5c) the last FISCAL-YEAR actual — the E base

    def growth(s: list[float | None]) -> list[str]:
        out = ["—"]
        for i in range(1, len(s)):
            if bases[i] == "est":
                # (D5c) an FY estimate's growth is vs the PRIOR FISCAL YEAR (a like period), NOT the
                # overlapping LTM: the first E col compares to the last FY actual, later E cols to
                # the prior E col. The base FY is named ("+4% (vs FY25)").
                j = i - 1 if bases[i - 1] == "est" else prior_fy
                base = s[j] if j is not None else None
                v = s[i]
                if v is None or base is None or not base or j is None:
                    out.append("—")
                    continue
                pct = f"{(v / base - 1) * 100:+.0f}%"
                out.append(pct if bases[j] == "est" else f"{pct} (vs {columns[j].split()[0]})")
                continue
            v, prev = s[i], s[i - 1]
            if v is None or prev is None or not prev:
                out.append("—")
            elif bases[i] != bases[i - 1]:
                out.append("— (basis)")
            else:
                out.append(f"{(v / prev - 1) * 100:+.0f}%")
        return out

    def margin(num: list[float | None], den: list[float | None]) -> list[str]:
        return [
            f"{n / d * 100:.0f}%" if n is not None and d is not None and d else "—"
            for n, d in zip(num, den, strict=False)
        ]

    rev = series("Total Revenue", "Revenue")
    if not any(v is not None for v in rev):
        return Sourced.unknown(note="Income Statement (annual): no Total Revenue — core row absent")
    ebitda = series("EBITDA", "EBITDA")
    rows: list[FinRow] = [
        FinRow(label="Revenue ($M)", cells=[_fmt_m(v) for v in rev]),
        FinRow(label="Revenue growth", cells=growth(rev)),
        FinRow(label="EBITDA ($M)", cells=[_fmt_m(v) for v in ebitda]),
        FinRow(label="EBITDA margin", cells=margin(ebitda, rev)),
    ]
    for disp_lbl, is_lbl, est_metric, fmt in _C1_ROWS[2:]:
        s = series(is_lbl, est_metric)
        fn = _fmt_eps if fmt == "e" else _fmt_m
        unit = "" if fmt == "e" else " ($M)"
        rows.append(FinRow(label=disp_lbl + unit, cells=[fn(v) for v in s]))
    # C4 cash-flow essentials (actuals only; no consensus E), matched to the displayed column by
    # FISCAL-PERIOD identity (short, is_ltm) with collision detection — NOT the bare short, and NOT
    # the Reclassified flag: CIQ tags a P&L reclassification on the Income Statement but not the
    # Cash Flow for the SAME fiscal year, so a basis match would drop valid CF values (real
    # case: MVST FY22/FY23). A genuine duplicate column (same (short, is_ltm) twice — a restated AND
    # an as-reported copy) is ambiguous, so it drops to "—" (fail loud) rather than silently keeping
    # whichever landed last in the lookup dict.
    try:
        cf = bundle.sheet("financials", "Cash Flow", freq="annual")
        cf_hdr = _period_header(cf)
        cf_map: dict[tuple[str, bool], int] = {}
        cf_dupe: set[tuple[str, bool]] = set()
        if cf_hdr is not None:
            for cc, sh, lt, _cr in _fin_periods(cf[cf_hdr]):
                key = (sh, lt)
                if key in cf_map:
                    cf_dupe.add(key)
                cf_map[key] = cc

        def cf_cell(ri: int | None, key: tuple[str, bool]) -> str:
            j = cf_map.get(key)
            if ri is None or j is None or key in cf_dupe or j >= len(cf[ri]):
                return "—"
            return _fmt_m(clean_num(cf[ri][j]))

        for disp_lbl, cf_lbl in _C1_CF:
            cf_ri = _find_row(cf, cf_lbl)
            cells = [cf_cell(cf_ri, (sh, lt)) for _c, sh, lt, _cr in disp] + ["—", "—"]
            if any(c != "—" for c in cells):
                rows.append(FinRow(label=disp_lbl + " ($M)", cells=cells))
    except CiqUnavailableError:
        pass
    est = as_of or "?"
    note = f"E = consensus (Estimates→Trends 'Current'), as-of {est}; (R) = Reclassified basis"
    return Sourced.present(
        FinTable(columns=columns, rows=rows, note=note),
        source_ref="CIQ Financials→Income Statement + Cash Flow (annual) + Estimates→Trends (FY E)",
    )


def _qmargin(num: list[float | None], den: list[float | None]) -> list[str]:
    return [
        f"{n / d * 100:.0f}%" if n is not None and d is not None and d else "—"
        for n, d in zip(num, den, strict=False)
    ]


def financial_summary_quarterly(bundle: CiqBundle) -> Sourced[FinTable]:
    """(C2) Trailing-8-quarter Income Statement — Revenue, gross margin %, EBITDA (if the quarterly
    export carries it, else the row is omitted and noted), EBITDA margin %, QoQ %, YoY % (same-basis
    ONLY — a Reclassified boundary reads '— (basis)'). Makes the Q1-2026 collapse visible."""
    try:
        rows = bundle.sheet("financials", "Income Statement", freq="quarterly")
    except CiqUnavailableError as exc:
        return _miss_or_unknown(bundle, "financials", exc)
    hdr = _period_header(rows)
    if hdr is None:
        return Sourced.unknown(note="Income Statement (quarterly): no Fiscal Period header")
    periods = _fin_periods(rows[hdr])[-8:]
    if len(periods) < 2:
        return Sourced.unknown(note="Income Statement (quarterly): fewer than 2 quarters")
    cols = [c for c, _s, _l, _r in periods]
    recl = [r for _c, _s, _l, r in periods]
    qtoks = [_quarter_token(rows[hdr][c]) for c in cols]  # Q1..Q4 per col, for the same-quarter YoY
    columns = [s + (" (R)" if r else "") for _c, s, _l, r in periods]

    def qrow(label: str) -> list[float | None]:
        ri = _find_row(rows, label)
        return [
            clean_num(rows[ri][c]) if ri is not None and c < len(rows[ri]) else None for c in cols
        ]

    rev = qrow("Total Revenue")
    if not any(v is not None for v in rev):
        return Sourced.unknown(note="Income Statement (quarterly): no Total Revenue")
    eb = qrow("EBITDA")
    frows: list[FinRow] = [
        FinRow(label="Revenue ($M)", cells=[_fmt_m(v) for v in rev]),
        FinRow(label="Gross margin", cells=_qmargin(qrow("Gross Profit"), rev)),
    ]
    ebitda_note = ""
    if any(v is not None for v in eb):
        frows.append(FinRow(label="EBITDA ($M)", cells=[_fmt_m(v) for v in eb]))
        frows.append(FinRow(label="EBITDA margin", cells=_qmargin(eb, rev)))
    else:
        ebitda_note = "EBITDA rows omitted — no quarterly EBITDA in this export. "
    qoq = ["—"]
    for i in range(1, len(rev)):
        v, prev = rev[i], rev[i - 1]
        if v is None or prev is None or not prev:
            qoq.append("—")
        elif recl[i] != recl[i - 1]:
            qoq.append("— (basis)")
        else:
            qoq.append(f"{(v / prev - 1) * 100:+.0f}%")
    yoy: list[str] = []
    for i in range(len(rev)):
        cur = rev[i]
        prior = rev[i - 4] if i >= 4 else None
        # YoY is same-quarter ONLY: col i and col i-4 must be the SAME fiscal quarter. A gap or a
        # duplicated/restated column would otherwise put a cross-quarter number under a "YoY" label.
        same_q = i >= 4 and qtoks[i] is not None and qtoks[i] == qtoks[i - 4]
        if cur is None or prior is None or not prior or not same_q:
            yoy.append("—")
        elif recl[i] != recl[i - 4]:
            yoy.append("— (basis)")
        else:
            yoy.append(f"{(cur / prior - 1) * 100:+.0f}%")
    frows += [FinRow(label="Revenue QoQ", cells=qoq), FinRow(label="Revenue YoY", cells=yoy)]
    return Sourced.present(
        FinTable(columns=columns, rows=frows,
                 note=ebitda_note + "QoQ/YoY same-basis only; (R) = Reclassified"),
        source_ref="CIQ Financials→Income Statement (quarterly, trailing 8Q)",
    )


def _bs_posture_build(bs: Rows, freq: str) -> Sourced[str] | None:
    """(C3) Build the posture string from ONE Balance Sheet grid, or None if cash is absent (so the
    caller can fall through to the other freq). Every line is read AT THE CASH COLUMN's period — a
    single as-of — so a partial latest quarter can't stitch a stale debt or a period-mixed net
    working capital under one 'as of' label (as-of discipline): a line blank at that column is
    omitted, never back-filled from an earlier period. Split out so ``balance_sheet_posture`` can
    address both freqs with string literals the CIQ-manifest drift guard can see."""
    hdr = _bs_period_header(bs)
    cash_ri = _find_row(bs, "Total Cash & ST Investments")
    anchor = _latest_col(bs, cash_ri, hdr) if cash_ri is not None else None
    if anchor is None:
        return None
    pj, cash_v, _ = anchor  # the ONE period every line below is reported at

    def at(label: str) -> float | None:  # value at the ANCHOR column (not the row's own latest)
        ri = _find_row(bs, label)
        return clean_num(bs[ri][pj]) if ri is not None and pj < len(bs[ri]) else None

    per = _fin_short(bs[hdr][pj]) if hdr is not None and pj < len(bs[hdr]) else "latest"
    parts = [f"cash & ST inv {_fmt_m(cash_v)}"]
    for lbl, key in (("total debt", "Total Debt"), ("net debt", "Net Debt")):
        if (v := at(key)) is not None:
            parts.append(f"{lbl} {_fmt_m(v)}")
    eq = at("Total Common Equity")
    if eq is None:
        eq = at("Total Equity")
    if eq is not None:
        parts.append(f"equity {_fmt_m(eq)}")
    tca, tcl = at("Total Current Assets"), at("Total Current Liabilities")
    if tca is not None and tcl is not None:
        parts.append(f"net working capital {_fmt_m(tca - tcl)}")
    parts.append("net-debt/EBITDA → see the Leverage & survival block (not recomputed)")
    return Sourced.present(
        f"as of {per} ($M): " + "; ".join(parts),
        source_ref=f"CIQ Financials→Balance Sheet ({freq}, {per})",
    )


def balance_sheet_posture(bundle: CiqBundle) -> Sourced[str]:
    """(C3) Balance-sheet posture at the latest period (period-labelled): cash, total debt, net
    debt, equity, net working capital (TCA − TCL). Net-debt/EBITDA is NOT recomputed — it cross-refs
    the unified leverage block. Prefers the freshest (quarterly) Balance Sheet."""
    unavailable: Exception | None = None
    try:  # literal freqs (not a loop var) so the CIQ-manifest drift guard can see the address
        if (got := _bs_posture_build(
            bundle.sheet("financials", "Balance Sheet", freq="quarterly"), "quarterly")):
            return got
    except CiqUnavailableError as exc:
        unavailable = exc
    try:
        if (got := _bs_posture_build(
            bundle.sheet("financials", "Balance Sheet", freq="annual"), "annual")):
            return got
    except CiqUnavailableError as exc:
        unavailable = exc
    return _miss_or_unknown(
        bundle, "financials", unavailable or CiqUnavailableError("Balance Sheet"))
