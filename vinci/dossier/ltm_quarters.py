"""THE LTM AGAINST ITS FOUR QUARTERS (2026-10-30, operator ruling "go ahead with this fix then").

THE DEFECT. CIQ builds the annual export's LTM column as the last fiscal year plus the current
year-to-date less the prior one. Nothing here checked the result against the quarters it is made
of, so a wrong LTM cell reached the page, the materiality guard and the anchor's LTM margin
exactly as a right one does. Two shapes, both measured 2026-10-30 on the `-ta` exports:

* a PRESS-RELEASE column (`ciq_sheets.require_filed_income_statement` refuses it): GOOGL's gain on
  investments read FY25's 24,620.0 in its LTM to Sep-30-2026, where its quarters sum to 138,156.0
  without Q3;
* a FILED column the status cannot see: NFLX's LTM to Sep-30-2026 reads a merger charge of
  -2,800.0 where its quarterly export books +2,800.0 in Q1 2026, and the quarters' pre-tax income
  and net income sum to the LTM's exactly.

THE STATUS GATE READS THE CAUSE; THIS IS THE PAIRED VALUE TEST (CLAUDE.md: pair every presence or
count guard with a check on the values). For each ADDITIVE Income Statement row on the annual
summary — revenue, EBITDA, EBIT, net income and the unusual items it surfaces, never a share count,
per-share figure, margin or growth — the LTM is compared with the sum of the quarterly export's
four quarters ending on the LTM's own date. The quarters are found BY DATE (`ciq_sheets.
header_period`), never by position.

WHAT IT DOES WITH WHAT IT FINDS. A row whose quarters disagree, carry a '-', or cannot be located
is a QA flag. It REFUSES only for a row the materiality guard demands the synthesis state
(item 19c's own selection): NKE's restructuring LTM -385.0 is right and its quarterly export is the
one with the gap, so a non-material disagreement never blocks.

A '-' QUARTER IS AN ABSENCE, NEVER A ZERO. The quarters that carry a figure are summed and that sum
is what is compared; a row whose '-' leaves it reconciling reads UNVERIFIED and is flagged, never
refused. Refusing on the '-' itself would select on the export's FORM: CIQ writes '-' for a quarter
with no such item on one row and 0.0 on the next (CNXC's goodwill impairment, -1,523.3 and
-1,050.0 in two quarters, '-' in one and 0.0 in another, sums to its LTM of -2,573.3 exactly).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Literal

from vinci.dossier import ciq_sheets as cs
from vinci.dossier.ciq import CiqBundle, CiqUnavailableError, clean_num
from vinci.dossier.materiality import MaterialityUnavailableError, unusual_items_block
from vinci.dossier.schemas import FinTable

#: ABOUT 2%, SET BY FACE VALIDITY (operator ruling 2026-10-30) and never tuned on an outcome:
#: restated prior-year comparatives legitimately move a filed LTM 1-2% off its quarters (measured
#: on LLY's, NKE's and CNXC's filed columns).
TOLERANCE = 0.02
#: HALF THE UNIT THE PAGE PRINTS. The annual summary prints $M to the whole million, so a gap under
#: half of one cannot reach the page — the floor below which a ratio of two near-zero figures is
#: not a disagreement (a 0.0 LTM against quarters summing to -0.004 is 100% apart).
PRINT_SLACK_MUSD = 0.5
#: The QA marker every flag opens with (`flags._QA_MARKERS`).
FLAG_PREFIX = "ciq-ltm-quarters:"

Outcome = Literal["agree", "differ", "unverified", "not_run"]

#: The annual summary's additive core rows → the Income Statement label each is read from
#: (`ciq_sheets._C1_ROWS`, money rows only: never an EPS row).
_CORE: dict[str, str] = {f"{disp} ($M)": is_lbl for disp, is_lbl, _est, fmt in cs._C1_ROWS
                         if fmt == "m"}


@dataclass(frozen=True)
class QuarterCell:
    """One of the four quarters, as the quarterly export's header dates it."""

    end: date
    quarter: int | None
    value: float | None  # None: the cell is '-', or the row is absent from the quarterly sheet


@dataclass(frozen=True)
class LtmCheck:
    """One annual-summary row's LTM against its four quarters."""

    label: str                         # the annual summary's row label
    ltm: float
    ltm_end: date
    quarters: tuple[QuarterCell, ...]  # empty when they could not be located
    outcome: Outcome
    reason: str | None = None          # why it did not run (outcome "not_run")

    @property
    def carried(self) -> float | None:
        """The sum of the quarters that carry a figure, or None when none does."""
        vals = [q.value for q in self.quarters if q.value is not None]
        return sum(vals) if vals else None

    def flag(self) -> str:
        head = (f"{FLAG_PREFIX} {self.label} — the LTM to {self.ltm_end:%Y-%m-%d} reads "
                f"{self.ltm:,.1f}")
        if self.outcome == "not_run":
            return f"{head}; NOT CHECKED against its quarters: {self.reason}"
        cells = " + ".join(
            f"{'-' if q.value is None else f'{q.value:,.1f}'} "
            f"(Q{q.quarter or '?'} {q.end:%Y-%m-%d})" for q in self.quarters)
        n = sum(1 for q in self.quarters if q.value is not None)
        carried = self.carried if self.carried is not None else 0.0
        body = (f"{head}, the four quarters ending then {cells} = {carried:,.1f}"
                + ("" if n == len(self.quarters) else f" on the {n} carrying a figure"))
        if self.outcome == "differ":
            gap = abs(self.ltm - carried)
            return (f"{body}: DIFFER by {gap:,.1f} $M, "
                    f"{gap / max(abs(self.ltm), abs(carried)):.2%} (tolerance "
                    f"{TOLERANCE:.0%}, or {PRINT_SLACK_MUSD} $M)")
        dash = ", ".join(f"Q{q.quarter or '?'} {q.end:%Y-%m-%d}"
                         for q in self.quarters if q.value is None)
        return f"{body}, which reconciles; UNVERIFIED, because {dash} read(s) '-'"


@dataclass(frozen=True)
class LtmQuarterRead:
    """Every row checked, and why no row was checked at all when that is so."""

    rows: tuple[LtmCheck, ...]
    not_run: str | None = None

    def flags(self) -> list[str]:
        """One QA flag per row that does not agree, and one when nothing was checked. Every one
        is listed — none is cut."""
        out = [r.flag() for r in self.rows if r.outcome != "agree"]
        if self.not_run is not None:
            out.append(f"{FLAG_PREFIX} NOT RUN — {self.not_run}")
        return out

    def refused(self, material: set[str]) -> list[LtmCheck]:
        """The rows that stop the build: a MATERIAL row whose quarters disagree, or which could
        not be checked at all — never one merely carrying a '-' that still reconciles."""
        return [r for r in self.rows
                if r.label in material and r.outcome in ("differ", "not_run")]


def refusal_message(ticker: str, rows: list[LtmCheck]) -> str:
    return (f"{ticker}: {len(rows)} MATERIAL annual-summary row(s) whose LTM the quarterly export "
            "does not support — " + "; ".join(r.flag()[len(FLAG_PREFIX) + 1:] for r in rows)
            + ". The page would print this LTM, and the synthesis is asked to state it; the "
            "quarterly side can be the wrong one (NKE's restructuring), so read both exports "
            "before re-exporting, and re-run once they agree")


def _additive_rows(inc: list[list[Any]], table: FinTable) -> list[tuple[str, int]]:
    """(summary label, annual row index) for each ADDITIVE Income Statement row the annual summary
    carries: the core money rows by the label the summary reads them from (`_C1_ROWS`), and every
    unusual item it surfaces, from inside the sheet's own block, as the summary takes it."""
    where: dict[str, int] = {}
    for label, is_lbl in _CORE.items():
        if (ri := cs._find_row(inc, is_lbl)) is not None:
            where[label] = ri
    try:
        lo, hi = unusual_items_block(inc)
    except MaterialityUnavailableError:
        lo = hi = 0
    for ri in range(lo, hi):
        lbl = str(inc[ri][0] or "").strip() if inc[ri] else ""
        if lbl:
            where.setdefault(f"{lbl} ($M)", ri)
    return [(r.label, where[r.label]) for r in table.rows if r.label in where]


def _quarter_row(q: list[list[Any]], sheet_label: str, unusual: bool) -> int | None:
    """The quarterly sheet's row of the same name — inside its own unusual-items block for an
    unusual item, as the annual one was read."""
    if not unusual:
        return cs._find_row(q, sheet_label)
    try:
        lo, hi = unusual_items_block(q)
    except MaterialityUnavailableError:
        return None
    return next((i for i in range(lo, hi)
                 if q[i] and str(q[i][0] or "").strip() == sheet_label), None)


def _four_quarters(q: list[list[Any]], hdr: int,
                   end: date) -> tuple[list[tuple[int, cs.HeaderPeriod]] | None, str | None]:
    """The quarterly columns of the four quarters ending on ``end``, oldest first, each found by
    the month its header's date is named for — or None and why, when a quarter has no column or
    two."""
    last = cs._nominal_month(end)
    slots: dict[int, list[tuple[int, cs.HeaderPeriod]]] = {last - 3 * k: [] for k in range(4)}
    for j in range(1, len(q[hdr])):
        p = cs.header_period(q[hdr][j])
        if p.kind == "Q" and p.end is not None and cs._nominal_month(p.end) in slots:
            slots[cs._nominal_month(p.end)].append((j, p))
    bad = [(m, cols) for m, cols in sorted(slots.items()) if len(cols) != 1]
    if bad:
        what = "; ".join(
            f"{'no column' if not cols else f'{len(cols)} columns'} for the quarter named for "
            f"{(m // 12):04d}-{m % 12 + 1:02d}" for m, cols in bad)
        return None, f"the quarterly Income Statement has {what}"
    return [slots[m][0] for m in sorted(slots)], None


def check(bundle: CiqBundle, table: FinTable | None) -> LtmQuarterRead:
    """Each additive annual-summary row's LTM against the four quarters ending on its date."""
    if table is None:
        return LtmQuarterRead((), "the annual summary is UNKNOWN, so no row reached it")
    try:
        inc = bundle.sheet("financials", "Income Statement", freq="annual")
    except CiqUnavailableError as exc:
        return LtmQuarterRead((), f"no annual Income Statement ({exc})")
    hdr = cs._period_header(inc)
    head: list[Any] = inc[hdr] if hdr is not None else []
    ltm = [(c, cs.header_period(head[c])) for c, _s, is_ltm, _r in cs._fin_periods(head)
           if is_ltm][:1]
    if not ltm:
        return LtmQuarterRead((), "the annual Income Statement carries no LTM column, so the "
                                  "summary's latest column is a fiscal year and there is no "
                                  "trailing figure to check")
    col, period = ltm[0]
    if period.end is None:
        return LtmQuarterRead((), "the annual Income Statement's LTM header states no date")
    rows = _additive_rows(inc, table)
    located: list[tuple[int, cs.HeaderPeriod]] | None = None
    why: str | None = None
    q: list[list[Any]] = []
    try:
        q = bundle.sheet("financials", "Income Statement", freq="quarterly")
        qhdr = cs._period_header(q)
        if qhdr is None:
            why = "the quarterly Income Statement has no Fiscal Period header"
        else:
            located, why = _four_quarters(q, qhdr, period.end)
    except CiqUnavailableError as exc:
        why = f"no quarterly Income Statement ({exc})"
    out: list[LtmCheck] = []
    for label, ri in rows:
        value = clean_num(inc[ri][col]) if col < len(inc[ri]) else None
        if value is None:
            continue   # the summary prints no LTM here, so there is no figure to check
        if located is None:
            out.append(LtmCheck(label, value, period.end, (), "not_run", why))
            continue
        sheet_label = _CORE.get(label, str(inc[ri][0]).strip())
        qi = _quarter_row(q, sheet_label, unusual=label not in _CORE)
        if qi is None:
            out.append(LtmCheck(label, value, period.end, (), "not_run",
                                f"the quarterly Income Statement carries no '{sheet_label}' row"
                                + ("" if label in _CORE else " inside its unusual-items block")))
            continue
        cells = tuple(
            QuarterCell(p.end, p.quarter,
                        clean_num(q[qi][j]) if j < len(q[qi]) else None)
            for j, p in located if p.end is not None)
        out.append(_judge(label, value, period.end, cells))
    return LtmQuarterRead(tuple(out))


def _judge(label: str, ltm: float, end: date, cells: tuple[QuarterCell, ...]) -> LtmCheck:
    present = [c.value for c in cells if c.value is not None]
    if not present:
        return LtmCheck(label, ltm, end, cells, "not_run",
                        "no quarter carries a figure for it in the quarterly export")
    carried = sum(present)
    gap = abs(ltm - carried)
    if gap > max(TOLERANCE * max(abs(ltm), abs(carried)), PRINT_SLACK_MUSD):
        return LtmCheck(label, ltm, end, cells, "differ")
    if len(present) < len(cells):
        return LtmCheck(label, ltm, end, cells, "unverified")
    return LtmCheck(label, ltm, end, cells, "agree")
