"""CIQ'S REVENUE AND OPERATING CASH FLOW, SET AGAINST THE FILINGS — every actual column of the
annual table (each fiscal year, and the LTM) against the same period rebuilt from XBRL.

WHY (2026-10-26). The financial summary's Revenue and CFO rows are the most-read figures on a
page, and nothing set them against the filings: revenue reached a check only inside a margin
(`anchor.midcycle_gap`) and a guide (`guide_verification_check`), and cash flow only as the SIGN of
CIQ's LTM levered FCF against the sign of one quarter's OCF — two measures over two periods
(`self_funding_check`). The data-quality scorecard reads this block (`revenue_vs_xbrl`,
`ocf_vs_xbrl`). Measured before it was built, on the 27 committed pages: CIQ carries the filer's
LATEST-filed figure (LLY's and UBER's restated years, AMZN's and V's restated cash flow), to the
dollar wherever both sides report the period.

THE PERIOD IS CIQ'S OWN, read off the export's period header — the header the table's columns come
from — and never off a column label: a 52/53-week filer can end two fiscal years in one calendar
year, and a label carries only the year.

THE FILING FIGURE IS THE PLAINEST THE TAGS ALLOW, on ONE tag (never spliced), USD facts only, as
filed by a date (assembly's, so a later restatement never reads as CIQ's error):

* a fiscal year — the filer's ~12-month fact ending on that date;
* the LTM — a ~12-month fact ending on that date (a 10-K's year, or a 10-Q's own trailing column,
  as Amazon files its cash flow), else the fiscal year before it + the year-to-date − the prior
  year-to-date. A 10-Q tags cash flow, and often revenue, year-to-date only.

The tag is the first alias of the concept (`CONCEPT_ALIASES`, ordered by meaning) that reports the
period. A period no alias reports is stated per row and never rebuilt from a guess.

A DIFFERENCE THE FILINGS EXPLAIN IS NAMED, NEVER INFERRED: where CIQ differs from that figure but
equals another alias's for the same period, or an earlier filing's for the fiscal year (the filer
has restated it since), the row names the tag or the accession. Evidence for the reader, not a
correction this code makes.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from vinci.dossier.ciq import CiqBundle, CiqUnavailableError, clean_num, excel_date
from vinci.dossier.ciq_sheets import _C1_CF, _fin_periods, _find_row, _period_header
from vinci.dossier.schemas import MechanicalLayer, StatementReconciliation, StatementReconRow
from vinci.edgar.concepts import CONCEPT_ALIASES, ConceptPoint, points_for_tag

#: A figure CIQ copies off the statement differs from the filing only by rounding — CIQ keeps three
#: decimals of $M. Half a percent is far past any rounding, and the $1M floor (`ebitda_recon`'s)
#: keeps a small filer's rounding (a −$2.6M year's cents) from reading as a difference.
DIFFERENT_SHARE = 0.005
DIFFERENT_FLOOR = 1.0
_SAME_END_DAYS = 7
#: A year-to-date runs one to three quarters; a year shift lands within this many days of 365.
_YTD_DAYS = (80, 290)
_YEAR_SLACK_DAYS = 10
_USD = "USD"
FISCAL_YEAR = "fiscal year"
TRAILING = "the filer's own twelve-month figure (10-Q)"
COMPOSED = "fiscal year + year-to-date − prior year-to-date"
SOURCE_REF = ("CIQ Financials (Annual)→Income Statement 'Total Revenue' and →Cash Flow 'Cash from "
              "Ops.' against EDGAR XBRL (the first revenue / operating-cash-flow alias reporting "
              "the period)")


@dataclass(frozen=True)
class Line:
    key: str            # the row's `line`
    label: str          # the annual table's row label
    ciq_row: str        # CIQ's row label (Income Statement, then Cash Flow)
    concept: str        # the `CONCEPT_ALIASES` key


#: The two rows, read as `ciq_sheets.financial_summary_annual` reads them.
LINES: tuple[Line, ...] = (
    Line("revenue", "Revenue ($M)", "Total Revenue", "revenue"),
    Line("operating_cash_flow", f"{_C1_CF[0][0]} ($M)", _C1_CF[0][1], "operating_cash_flow"),
)
_BY_KEY = {ln.key: ln for ln in LINES}


@dataclass(frozen=True)
class CiqFigure:
    line: str
    column: str         # the annual table's column label
    period_end: date
    is_ltm: bool
    value: float        # $M


def _end(cell: Any) -> date | None:
    """A period-header cell → its end date: an Excel serial, or stacked text whose LAST line is
    the date ('12 months\\nJan-31-2026', 'LTM\\n12 months\\nAug-01-2026')."""
    if isinstance(cell, (int, float)) and not isinstance(cell, bool):
        return excel_date(cell)
    text = str(cell or "").strip()
    return excel_date(text.splitlines()[-1].strip()) if text else None


def ciq_figures(bundle: CiqBundle) -> list[CiqFigure]:
    """Every actual figure of the annual table's Revenue and CFO rows, with its column label and the
    end date CIQ's header states — the columns `financial_summary_annual` shows (each fiscal year,
    then the first LTM), the cash-flow sheet matched to them as it matches them (by fiscal-period
    identity; a duplicated column is dropped). Raises `CiqUnavailableError` without the income
    statement; a missing cash-flow sheet leaves only revenue."""
    inc = bundle.sheet("financials", "Income Statement", freq="annual")
    hi = _period_header(inc)
    if hi is None:
        return []
    hdr = inc[hi]
    periods = _fin_periods(hdr)
    # a label two columns share (two fiscal years ending in one calendar year) names no one period:
    # neither column is read, here or in `table_figures`
    disp = [(c, s, s + (" (R)" if r else ""), lt) for c, s, lt, r in
            [p for p in periods if not p[2]] + [p for p in periods if p[2]][:1]]
    labels = [lbl for _c, _s, lbl, _lt in disp]
    disp = [d for d in disp if labels.count(d[2]) == 1]
    out: list[CiqFigure] = []
    ri = _find_row(inc, LINES[0].ciq_row)
    for c, _short, label, ltm in disp:
        v = clean_num(inc[ri][c]) if ri is not None and c < len(inc[ri]) else None
        if v is not None and (end := _end(hdr[c])) is not None:
            out.append(CiqFigure(LINES[0].key, label, end, ltm, v))
    try:
        cf = bundle.sheet("financials", "Cash Flow", freq="annual")
    except CiqUnavailableError:
        return out
    chi = _period_header(cf)
    if chi is None:
        return out
    cf_hdr = cf[chi]
    cols: dict[tuple[str, bool], int] = {}
    dupe: set[tuple[str, bool]] = set()
    for cc, sh, lt, _r in _fin_periods(cf_hdr):
        if (sh, lt) in cols:
            dupe.add((sh, lt))
        cols[(sh, lt)] = cc
    cri = _find_row(cf, LINES[1].ciq_row)
    for _c, short, label, ltm in disp:
        key = (short, ltm)
        j = cols.get(key)
        if cri is None or j is None or key in dupe or j >= len(cf[cri]):
            continue
        v = clean_num(cf[cri][j])
        if v is not None and (end := _end(cf_hdr[j])) is not None:
            out.append(CiqFigure(LINES[1].key, label, end, ltm, v))
    return out


def table_figures(table: Any) -> dict[tuple[str, str], float]:
    """{(line, column): $M} — the page's OWN annual-table values for the two rows, actual columns
    only. What a stored block must agree with to be the page's (the back-fill's proof, and the
    scorecard's staleness guard)."""
    if not isinstance(table, dict):
        return {}
    cols = [str(c) for c in table.get("columns") or []]
    est = table.get("is_estimate") or []
    rows = {r.get("label"): r for r in table.get("rows") or [] if isinstance(r, dict)}
    out: dict[tuple[str, str], float] = {}
    for ln in LINES:
        vals = (rows.get(ln.label) or {}).get("values") or []
        for i, col in enumerate(cols):
            if i < len(vals) and not (i < len(est) and est[i]) and cols.count(col) == 1:
                v = vals[i]
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    out[(ln.key, str(col))] = float(v)
    return out


def _days(p: ConceptPoint) -> int:
    return (p.period_end - p.period_start).days if p.period_start is not None else -1


def _near(a: date, b: date, days: int = _SAME_END_DAYS) -> bool:
    return abs((a - b).days) <= days


def _latest(pts: list[ConceptPoint]) -> ConceptPoint:
    return max(pts, key=lambda p: (p.filed, p.accession or ""))


def _year(pts: list[ConceptPoint], end: date) -> list[ConceptPoint]:
    return [p for p in pts if p.is_annual and _near(p.period_end, end)]


def _on_tag(pts: list[ConceptPoint], end: date, is_ltm: bool,
            ) -> tuple[float, str, ConceptPoint] | None:
    """($, construction, the point whose filing carries it) for the period, on one tag's points."""
    if twelve := _year(pts, end):
        p = _latest(twelve)
        return p.value, (TRAILING if (p.form or "").upper().startswith("10-Q") else FISCAL_YEAR), p
    if not is_ltm:
        return None
    ytds = [p for p in pts if _near(p.period_end, end) and _YTD_DAYS[0] <= _days(p) <= _YTD_DAYS[1]]
    for start in sorted({p.period_start for p in ytds if p.period_start is not None}):
        # the EARLIEST start is the longest year-to-date — the one that runs from the year's start
        ytd = _latest([p for p in ytds if p.period_start == start])
        fy = _year(pts, start - timedelta(days=1))
        if not fy:
            continue
        f = _latest(fy)
        f_start = f.period_start or start            # an annual point always carries its start
        prior = [p for p in pts if p.period_start is not None
                 and _near(p.period_start, f_start)
                 and _near(p.period_end, ytd.period_end - timedelta(days=365), _YEAR_SLACK_DAYS)
                 and abs(_days(p) - _days(ytd)) <= _YEAR_SLACK_DAYS]
        if prior:
            return f.value + ytd.value - _latest(prior).value, COMPOSED, ytd
    return None


def _differs(ciq: float, filing: float) -> bool:
    gap = abs(ciq - filing)
    return gap > DIFFERENT_SHARE * abs(filing) and gap >= DIFFERENT_FLOOR


def _row(fig: CiqFigure, facts: dict[str, Any], filed_by: date) -> StatementReconRow:
    concept = _BY_KEY[fig.line].concept
    base = {"line": fig.line, "column": fig.column, "period_end": fig.period_end.isoformat(),
            "ciq": fig.value, "is_ltm": fig.is_ltm}
    by_tag = {tag: [p for p in points_for_tag(facts, tag) if p.unit == _USD
                    and p.period_start is not None and p.filed <= filed_by]
              for tag in CONCEPT_ALIASES[concept]}
    built = [(tag, r) for tag, pts in by_tag.items()
             if (r := _on_tag(pts, fig.period_end, fig.is_ltm)) is not None]
    if not built:
        return StatementReconRow(**base, note=(
            f"no {concept} fact for this period on any alias tag, as filed by {filed_by}"
            + (" (no twelve-month figure, and no fiscal year with both year-to-dates on one tag)"
               if fig.is_ltm else "")))
    tag, (value, how, point) = built[0]
    filing = value / 1e6
    different = _differs(fig.value, filing)
    other = earlier = None
    if different:
        other = next((t for t, (v, _h, _p) in built[1:] if not _differs(fig.value, v / 1e6)), None)
        if other is None and not fig.is_ltm:
            earlier = next((p.accession for p in sorted(_year(by_tag[tag], fig.period_end),
                                                        key=lambda p: (p.filed, p.accession or ""))
                            if p.accession != point.accession
                            and not _differs(fig.value, p.value / 1e6)), None)
    return StatementReconRow(
        **base, filing=round(filing, 3), construction=how, tag=tag, accession=point.accession,
        gap=round(fig.value - filing, 3), different=different, other_tag=other,
        earlier_accession=earlier)


def reconcile(figures: list[CiqFigure], facts: dict[str, Any] | None, *,
              filed_by: date) -> StatementReconciliation | None:
    """Each figure against the filings, as filed by ``filed_by``. None with no EDGAR facts or no
    CIQ figure — nothing to set side by side, a different fact from a period the filings do not
    carry (stated per row)."""
    if facts is None or not figures:
        return None
    return StatementReconciliation(rows=[_row(f, facts, filed_by) for f in figures],
                                   as_filed_by=filed_by.isoformat(), source_ref=SOURCE_REF)


def attach(mech: MechanicalLayer, bundle: CiqBundle | None, facts: dict[str, Any] | None, *,
           filed_by: date) -> MechanicalLayer:
    """`mech` with `financial_summary.statement_reconciliation` built from the same export the
    table was — absent (never null) where the export or the facts are."""
    fs = mech.financial_summary
    if fs is None or bundle is None:
        return mech
    try:
        figures = ciq_figures(bundle)
    except CiqUnavailableError:
        return mech
    rec = reconcile(figures, facts, filed_by=filed_by)
    return mech.model_copy(update={
        "financial_summary": fs.model_copy(update={"statement_reconciliation": rec})})
