"""THE FILING DECIDES WHEN CIQ DISAGREES WITH ITSELF ON A MATERIAL LTM (2026-11-04, operator
approval: the SEC filing is the tiebreaker, the way an expert team builds a line from the 10-K and
10-Qs when its data vendor disagrees with itself).

THE DEFECT. Before any spend, assembly checks each material annual-summary row's LTM in CIQ's annual
export against its four quarters in CIQ's quarterly export, and refuses on a disagreement over 2%
(`ltm_quarters`). That check compares CIQ only with CIQ, so an inconsistency inside the vendor
blocks a name for as long as the vendor keeps it. CELH has been refused on it since 2026-11-02: its
Other Unusual Items read -418.8 in the annual LTM to 2026-06-30 and -405.0 over the quarterly
export's four quarters (`docs/records/2026-11-02-mnst-and-celh-followed-neither-page-built.md`).

THE RULE. For a MATERIAL row whose two CIQ readings DIFFER, the filer's own XBRL figure for the same
four quarters decides. If it reproduces at least one of CIQ's readings, the page states the FILED
figure, source-bound to every accession it was read from, with a main-body caveat naming CIQ's
disagreement (`FiledLtmFigure`). Where no filed figure can be read for the row, assembly refuses
exactly as before, and the refusal says why the filing could not decide.

THE MAPPING IS EXPLICIT AND REVIEWED (:data:`MAPPING`). A CIQ row label maps to us-gaap concepts
written out by hand, each with its sign stated, and nothing is matched fuzzily. An unmapped row
refuses. The FIRST mapped concept that carries all four quarters is the filed figure. It is never
spliced across concepts, never summed with another, and never passed over for a later concept
because a later one agrees better. Choosing among candidates by which one agrees would make the
agreement test pick its own evidence.

A CONTAINING LINE ONLY PICKS A CIQ READING (:data:`CONTAINING`; operator ruling 2026-11-04, "NFLX:
B"). Some filers tag an item only inside a wider line. NFLX's $2.8B WBD termination fee sits in
`NonoperatingIncomeExpense`, its whole "interest and other income (expense)" line. CIQ splits that
line above its unusual-items block into interest and investment income, currency gains and other
non-operating, so no unusual-items row is the whole line. The line's total is never stated as the
row: over NFLX's LTM it is 2,992.3, about 190M of interest and currency beyond the fee. It is used
only to pick WHICH CIQ reading the filing supports:
- Each named component row plus the row itself, in the quarterly export, must reproduce the filed
  line in EVERY quarter of the window, within half a printed million (:data:`BREAKDOWN_SLACK_MUSD`).
- If they do, the page states CIQ's quarterly READING, cited to the filings, and the caveat names
  the annual export's reading.
- One quarter that misses refuses.
NFLX reconciles in all four quarters to 2026-09-30, within 0.04 $M (Q1 2026: 70.0 - 8.3 - 9.5 +
2,800.0 against 2,852.166 filed, 10-Q 0001065280-26-000138). CELH's merger row misses by 2.9 to
22.9 $M a quarter and refuses.

The filed TOTAL alone cannot tell NFLX's two exports apart. The annual export reaches the same LTM
total by carrying +5,554.7 under Other Non-Operating, where the quarterly export's quarters carry
-27.0: its -2,800.0 row is offset there. What decides is the breakdown quarter by quarter, which
only the quarterly export offers, and which is the operator's rule. The caveat says so on the page.

THE QUARTERS are read as filed by the page's price date (`concepts.facts_as_of`, cut once at
:func:`decide`'s entry), so a filing made after the page's close never decides it. Each quarter is
the filer's 3-month fact ending within a week of CIQ's quarter end. Where there is none, it is the
longer period ending there less the period one quarter shorter from the same start (Q4 = the 10-K's
year less the nine months, Q2 = H1 less Q1), on the ONE tag, as `ebitda_recon._quarter` derives it.
A quarter the filer did not tag is an absence, never a zero, so the row refuses.

THE BAND, SET BY FACE VALIDITY AND NEVER BY OUTCOMES. The filed figure is accepted as the same
economic item only when it reproduces at least one of CIQ's two readings within the tolerance at
which CIQ is deemed to agree with itself: 2%, or half a printed million (`ltm_quarters.agrees`, the
operator's 2026-10-30 ruling). The reasoning:
- CIQ copies its figures off the filings, so a filed line that reproduces neither reading is not
  demonstrably the line CIQ read.
- A wider band would let a neighbouring item stand in for the row. NFLX's containing line sits 6.4%
  from +2,800, for example.
- A narrower band would refuse ordinary restated comparatives, which move a filed LTM 1-2%.
Sign is part of the test. A filed figure of the opposite sign to both readings is far from both by
construction, and refuses. CELH's filed -412.7 is 1.4% from the annual reading and 1.9% from the
quarterly one, so it reproduces both.

DOES THIS SELECT ON FORM? (CLAUDE.md, before any new gate.) It adjudicates between two vendor
readings by the primary source. It ranks nothing, grades nothing, and moves no weight, verdict or
proposal. One narrow selection is real and is stated here: WHICH refused names it can clear depends
on how the filer tags the item in XBRL. CELH tags its charge as `RestructuringCharges`, and NFLX's
fee sits inside a containing line CIQ's quarterly rows reproduce. WAT's merger costs and NKE's
restructuring are tagged under no mapped concept for every quarter in the window. That selection
decides only whether a page can be BUILT on a verified figure. A name it cannot clear is refused
exactly as before, so the selection can only ever leave a name where it was.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from vinci.dossier import ciq_sheets as cs
from vinci.dossier import ltm_quarters as lq
from vinci.dossier.ciq import CiqBundle, CiqUnavailableError, clean_num
from vinci.dossier.ciq_sheets import _fmt_m
from vinci.dossier.materiality import MaterialityUnavailableError, unusual_items_block
from vinci.dossier.schemas import (
    FiledLtmFigure,
    FiledLtmQuarter,
    MechanicalLayer,
    Sourced,
    Supports,
)
from vinci.edgar.concepts import ConceptPoint, _same_figure, facts_as_of, filed_at, points_for_tag

#: A filed period ends on CIQ's quarter end, or within a week of it (a 52/53-week filer's quarter
#: lands a few days off a calendar date, and CIQ names it by its fiscal end).
SAME_END_DAYS = 7
#: A quarter is 80-100 days — a 13-week quarter, or a 14-week one in a 53-week year.
QUARTER_DAYS = (80, 100)
#: HALF THE UNIT THE PAGE PRINTS — the repo's rounding floor (`ltm_quarters.PRINT_SLACK_MUSD`),
#: never set by an outcome. CIQ copies each component of a containing line off the same filing, so
#: a breakdown that is the filed line lands inside it in every quarter (NFLX's four: at most
#: 0.039 $M); one that misses by more is not that line (CELH's merger row: 2.9 to 22.9 $M).
BREAKDOWN_SLACK_MUSD = lq.PRINT_SLACK_MUSD


@dataclass(frozen=True)
class FiledLine:
    """The filed concepts one CIQ row maps to, and the sign that turns the filing into CIQ's."""

    tags: tuple[str, ...]   # us-gaap, in order of meaning; the first carrying every quarter is read
    sign: int               # CIQ's figure = sign × the filed figure
    why: str


#: CIQ's unusual-items rows print a CHARGE negative. The filer tags these concepts as an expense,
#: positive, so the sign is -1 for each. A credit the filer tags negative reads positive here.
#:
#: REVIEWED, ONE ENTRY AT A TIME. A row joins this map only with the concept that states it and the
#: reason it is the same item. The band catches a mapping that misreads a name, never a missing one.
MAPPING: dict[str, FiledLine] = {
    "Restructuring Charges ($M)": FiledLine(
        ("RestructuringCharges",), -1,
        "CIQ's restructuring row is the filer's restructuring charge"),
    "Other Unusual Items ($M)": FiledLine(
        ("RestructuringCharges",), -1,
        "CIQ files a restructuring charge it does not class as restructuring under Other Unusual "
        "Items — CELH's 2025-26 charge, tagged RestructuringCharges by the filer"),
    "Merger & Related Restruct. Charges ($M)": FiledLine(
        ("BusinessCombinationAcquisitionRelatedCosts",
         "BusinessCombinationIntegrationRelatedCosts"), -1,
        "CIQ's merger row is the filer's acquisition- or integration-related cost; a filer that "
        "splits the two across both tags is read on the first, and the band refuses it if that "
        "half reproduces neither CIQ reading — never summed into a figure no filing states"),
}


@dataclass(frozen=True)
class ContainingLine:
    """A filed line that CONTAINS a CIQ row, with the CIQ quarterly rows that make up the rest of
    it. It never states the row; it confirms CIQ's quarterly reading (module docstring)."""

    tag: str                       # the us-gaap concept of the whole line
    sign: int                      # CIQ's figure = sign × the filed figure
    components: tuple[str, ...]    # CIQ quarterly row labels, above the unusual-items block
    why: str


#: Read only when no same-item concept in :data:`MAPPING` carries every quarter. REVIEWED, ONE
#: ENTRY AT A TIME, like the map above.
CONTAINING: dict[str, ContainingLine] = {
    "Merger & Related Restruct. Charges ($M)": ContainingLine(
        "NonoperatingIncomeExpense", 1,
        ("Interest and Invest. Income", "Currency Exchange Gains (Loss)",
         "Other Non-Operating Inc. (Exp.)"),
        "NFLX files its $2.8B WBD termination fee only inside its 'interest and other income "
        "(expense)' line, which is CIQ's interest and investment income, currency and other "
        "non-operating rows plus the merger row. A filer whose line also holds interest expense or "
        "equity income reconciles in no quarter and refuses"),
}


@dataclass(frozen=True)
class Decision:
    """The filing's answer for one refused row: a figure, or why the filing cannot decide."""

    row: lq.LtmCheck
    figure: FiledLtmFigure | None
    reason: str | None = None
    #: (a containing line) what the annual export's own breakdown says, for the caveat
    note: str | None = None

    def caveat(self) -> str:
        """The main-body caveat: what the page states, where it was filed, and what CIQ said."""
        f = self.figure
        if f is None or f.value.value is None:
            raise ValueError("no filed figure — a refused row has no caveat, it has a refusal")
        if f.kind == "containing_line":
            return self._containing_caveat(f, f.value.value)
        a, q, v = f.ciq_annual, f.ciq_quarterly, f.value.value
        gap = abs(a - q) / max(abs(a), abs(q))
        n = sum(1 for c in self.row.quarters if c.value is not None)
        summed = ("four quarters" if n == len(self.row.quarters)
                  else f"{n} of {len(self.row.quarters)} quarters carrying a figure")
        sides = {"both": "both CIQ readings", "annual": "the annual export's reading",
                 "quarterly": "the quarterly export's reading"}[f.supports]
        return (f"FILED FIGURE STATED — {f.label}, LTM to {f.ltm_end}: the page states {v:,.1f}, "
                f"the SEC filings' us-gaap:{f.tag} over the four quarters as filed by "
                f"{f.as_filed_by} ({'; '.join(_accessions(f))}), because CIQ's two exports "
                f"disagree: the annual export's LTM reads {a:,.1f} and the quarterly export's "
                f"{summed} sum to {q:,.1f} ({gap:.1%} apart). The filed figure reproduces {sides} "
                f"(within {lq.TOLERANCE:.0%} or {lq.PRINT_SLACK_MUSD} $M): the quarters "
                + ", ".join(f"{x.value:,.1f} ({x.end}"
                            + (", a longer filed period less the one a quarter shorter"
                               if x.derived else "") + ")" for x in f.quarters)
                + f" sum to {v:,.1f}")

    def _containing_caveat(self, f: FiledLtmFigure, v: float) -> str:
        return (f"CIQ READING CONFIRMED BY THE FILING — {f.label}, LTM to {f.ltm_end}: the page "
                f"states {v:+,.1f}, the quarterly export's reading, because CIQ's two exports "
                f"disagree: the annual export's LTM reads {f.ciq_annual:+,.1f}. No filed concept "
                f"states the item alone; the filings carry it inside us-gaap:{f.tag}, a wider "
                f"line, and the quarterly export's breakdown of that line "
                f"({', '.join(f.components)} and this row) reproduces it in every quarter within "
                f"{BREAKDOWN_SLACK_MUSD} $M — "
                + "; ".join(f"{_breakdown_of(x):,.1f} against {x.value:,.3f} filed ({x.end})"
                            for x in f.quarters)
                + f" ({'; '.join(_accessions(f))}). " + (self.note or ""))


def _breakdown_of(x: FiledLtmQuarter) -> float:
    """A containing-line quarter's CIQ breakdown — RAISES on one that carries none, which only a
    hand-edited record could produce: a missing breakdown is never printed as a zero."""
    if x.ciq_breakdown is None:
        raise ValueError(f"the containing-line quarter to {x.end} carries no CIQ breakdown")
    return x.ciq_breakdown


def _accessions(f: FiledLtmFigure) -> list[str]:
    """Every distinct accession the four quarters were read from, in the order first read — off
    the structured field, never the rendered ``source_ref`` (which also names the FIRST filing a
    restated figure supersedes, a filing the figure was not read from)."""
    return list(dict.fromkeys(acc for x in f.quarters for acc in x.accessions))


def _days(p: ConceptPoint) -> int:
    return (p.period_end - p.period_start).days if p.period_start is not None else -1


def _latest(p: ConceptPoint) -> tuple[date, str]:
    """The latest filing of a period wins — a restatement known by the cut, as `ebitda_recon`."""
    return p.filed, p.accession or ""


def filed_quarter(points: list[ConceptPoint], end: date,
                  ) -> tuple[float, bool, tuple[ConceptPoint, ...]] | None:
    """($ as filed, derived, the point(s) read) — the discrete quarter ending ``end`` on one tag's
    points, or None when the filer stated nothing it can be read from.

    A DERIVED QUARTER IS READ FROM THE LATEST LONGER PERIOD and the latest shorter one filed on or
    before it, under TWO rules:

    - THE SHORTER IS NEVER A LATER COMPARATIVE (Codex, #891 round 2) — as
      `quality.sources.release._figures` pairs them. MVST's 9M-2024 non-operating line was restated
      from +7.864 to -0.293 in a 10-Q filed after its 10-K, and pairing the 10-K's year with that
      comparative stated a fourth quarter, 0.449, that no filing as of then stated (the 10-K's own:
      -7.708).
    - A RESTATED LONGER PERIOD IS NEVER PAIRED WITH A SHORTER ONE FILED BEFORE THE RESTATEMENT
      (review of #916, 2026-11-05). The first rule alone does not make the pair one basis: a
      10-K/A, an 8-K recast or a later 10-K can restate the YEAR before any restated nine months
      exist, and the whole restatement then lands in the quarter. UBER's FY2019 revenue was 14,147
      in its 10-K and 13,000 in its 8-K recast of 2021-01-14, while its nine months, 10,078, were
      filed before the recast: 13,000 − 10,078 = 2,922 is a fourth quarter on neither basis (as
      filed, 4,069). Such a quarter is None — an absence — never an older vintage read in its
      place. "Restated" is `concepts.superseded`'s rule, read off these points: the period's first
      filing stated another figure."""
    near = [p for p in points if p.period_start is not None
            and abs((p.period_end - end).days) <= SAME_END_DAYS]
    three = [p for p in near if QUARTER_DAYS[0] <= _days(p) <= QUARTER_DAYS[1]]
    if three:
        p = max(three, key=_latest)
        return p.value, False, (p,)
    for p in sorted((p for p in near if _days(p) > QUARTER_DAYS[1]), key=_latest,
                    reverse=True):
        shorter = [x for x in points if x.period_start == p.period_start and x.filed <= p.filed
                   and QUARTER_DAYS[0] <= (p.period_end - x.period_end).days <= QUARTER_DAYS[1]]
        if shorter:
            q = max(shorter, key=_latest)
            restated = _restated_on(points, p)
            if restated is not None and q.filed < restated:
                return None
            return p.value - q.value, True, (p, q)
    return None


def _restated_on(points: list[ConceptPoint], p: ConceptPoint) -> date | None:
    """The day ``p``'s own figure was first filed, where its period's FIRST filing (same tag, unit
    and dates, among ``points``) stated another figure — None when ``p`` restates nothing. A figure
    restated and restated back is the figure first filed (`concepts.superseded`)."""
    same = [x for x in points if x.unit == p.unit and x.period_start == p.period_start
            and x.period_end == p.period_end and x.filed <= p.filed]
    if _same_figure(min(same, key=_latest).value, p.value):
        return None
    return min(x.filed for x in same if _same_figure(x.value, p.value))


def ciq_readings_ref(row: lq.LtmCheck) -> str:
    """The ref a filed figure's two CIQ readings are cited by (item 29, option 4): the annual
    export's LTM cell, which the page's table no longer shows, and the quarterly export's quarters
    summed."""
    return (f"CIQ Financials — {row.label}, LTM to {row.ltm_end.isoformat()}: the annual export's "
            "LTM cell and the quarterly export's quarters summed")


def _quarter_ref(pts: tuple[ConceptPoint, ...], facts: dict[str, Any]) -> str:
    if len(pts) == 1:
        return filed_at(pts[0], facts)
    return f"{filed_at(pts[0], facts)} − {filed_at(pts[1], facts)}"


def decide(row: lq.LtmCheck, facts: dict[str, Any], *, as_filed_by: date,
           bundle: CiqBundle | None = None) -> Decision:
    """The filing's answer for one row ``ltm_quarters`` refuses. ``facts`` is the whole
    companyfacts blob; it is cut at ``as_filed_by`` here, before anything is read. ``bundle`` is
    the CIQ export the row was read from: a containing line is checked against its breakdown."""
    if row.outcome != "differ" or row.carried is None or not row.quarters:
        return Decision(row, None, "the filing decides between two CIQ readings, and the "
                                   "quarterly export gives no second reading here")
    line, wider = MAPPING.get(row.label), CONTAINING.get(row.label)
    if line is None and wider is None:
        return Decision(row, None, f"no reviewed mapping from the CIQ row {row.label!r} to a filed "
                                   "concept (`filed_tiebreak.MAPPING`, `CONTAINING`)")
    cut = facts_as_of(facts, as_filed_by)
    misses: list[str] = []
    for tag in line.tags if line is not None else ():
        pts = points_for_tag(cut, tag)
        got = [filed_quarter(pts, q.end) for q in row.quarters]
        if any(g is None for g in got):
            gone = ", ".join(q.end.isoformat() for q, g in zip(row.quarters, got, strict=True)
                             if g is None)
            misses.append(f"us-gaap:{tag} " + (f"states no quarter to {gone}" if pts else
                                                "carries no fact")
                          + f" as filed by {as_filed_by}")
            continue
        assert line is not None
        return _judge(row, line, tag, [g for g in got if g is not None], cut,
                      carried=row.carried, as_filed_by=as_filed_by)
    if wider is not None:
        pts = points_for_tag(cut, wider.tag)
        got = [filed_quarter(pts, q.end) for q in row.quarters]
        if any(g is None for g in got):
            gone = ", ".join(q.end.isoformat() for q, g in zip(row.quarters, got, strict=True)
                             if g is None)
            misses.append(f"the containing line us-gaap:{wider.tag} "
                          + (f"states no quarter to {gone}" if pts else "carries no fact")
                          + f" as filed by {as_filed_by}")
        elif bundle is None:
            misses.append(f"no CIQ export to set against the containing line us-gaap:{wider.tag}")
        else:
            return _judge_containing(row, wider, [g for g in got if g is not None], cut, bundle,
                                     carried=row.carried, as_filed_by=as_filed_by)
    return Decision(row, None, "no filed figure for every quarter — " + "; ".join(misses))


def _rows_above_block(sheet: list[list[Any]], labels: tuple[str, ...],
                      ) -> dict[str, int | None] | None:
    """{label: the row named ``label`` ABOVE the sheet's unusual-items block — where CIQ puts a
    non-operating component — or None when the sheet has no such row}; None when the sheet has no
    block to stand above. The block is located once per sheet."""
    try:
        lo, _hi = unusual_items_block(sheet)
    except MaterialityUnavailableError:
        return None
    above = sheet[:lo - 1]   # `lo` is the first row INSIDE the block; lo - 1 is its open subtotal
    return {lab: cs._find_row(above, lab) for lab in labels}


def _cell(sheet: list[list[Any]], ri: int | None, col: int) -> float | None:
    return clean_num(sheet[ri][col]) if ri is not None and col < len(sheet[ri]) else None


def _breakdown(row: lq.LtmCheck, wider: ContainingLine, bundle: CiqBundle,
               ) -> tuple[list[float], dict[str, tuple[float | None, float | None]],
                          float | None] | str:
    """(the quarterly export's breakdown of the line in each quarter, {component: (the annual
    export's LTM, the quarterly export's four quarters summed)}, the annual export's LTM breakdown)
    — or why it cannot be read. A component row the quarterly sheet LACKS refuses: it is never
    summed as a zero, nor named on the page as read. Within a row the sheet carries, a quarter's
    '-' adds nothing to that quarter's breakdown, which the filed line then checks; a component no
    quarter carries is None, never a summed 0, and an annual LTM the export does not state leaves
    the annual breakdown None — it is never totalled without it."""
    try:
        q = bundle.sheet("financials", "Income Statement", freq="quarterly")
        a = bundle.sheet("financials", "Income Statement", freq="annual")
    except CiqUnavailableError as exc:
        return f"no CIQ Income Statement to read the breakdown from ({exc})"
    qh, ah = cs._period_header(q), cs._period_header(a)
    if qh is None or ah is None:
        return "a CIQ Income Statement has no Fiscal Period header"
    four, why = lq._four_quarters(q, qh, row.ltm_end)
    if four is None:
        return why or "the quarterly columns could not be located"
    ltm = [c for c, _s, is_ltm, _r in cs._fin_periods(a[ah]) if is_ltm][:1]
    if not ltm:
        return "the annual Income Statement carries no LTM column"
    qrows = _rows_above_block(q, wider.components)
    if qrows is None:
        return "the quarterly Income Statement carries no unusual-items block to read above"
    if lacking := [lab for lab, ri in qrows.items() if ri is None]:
        return ("the quarterly Income Statement carries no "
                + ", ".join(f"'{lab}'" for lab in lacking) + " row above its unusual-items block")
    arows = _rows_above_block(a, wider.components) or dict.fromkeys(wider.components)
    per_q = [sum(v for v in [*(_cell(q, qrows[lab], j) for lab in wider.components), cell.value]
                 if v is not None)
             for (j, _p), cell in zip(four, row.quarters, strict=True)]
    parts: dict[str, tuple[float | None, float | None]] = {}
    for lab in wider.components:
        qvs = [v for j, _p in four if (v := _cell(q, qrows[lab], j)) is not None]
        parts[lab] = (_cell(a, arows[lab], ltm[0]), sum(qvs) if qvs else None)
    avs = [av for av, _qv in parts.values()]
    annual = (sum(av for av in avs if av is not None) + row.ltm
              if all(av is not None for av in avs) else None)
    return per_q, parts, annual


def _judge_containing(row: lq.LtmCheck, wider: ContainingLine,
                      got: list[tuple[float, bool, tuple[ConceptPoint, ...]]],
                      facts: dict[str, Any], bundle: CiqBundle, *, carried: float,
                      as_filed_by: date) -> Decision:
    """CIQ's quarterly reading, when its breakdown of the containing line is the filed line in
    every quarter; else why not. The line's own total is never the row's figure."""
    read = _breakdown(row, wider, bundle)
    if isinstance(read, str):
        return Decision(row, None, f"the containing line us-gaap:{wider.tag} cannot be set "
                                   f"against CIQ's breakdown: {read}")
    per_q, parts, annual = read
    quarters = [FiledLtmQuarter(end=q.end.isoformat(), value=round(wider.sign * v / 1e6, 3),
                                derived=derived, source_ref=_quarter_ref(pts, facts),
                                accessions=list(dict.fromkeys(
                                    p.accession for p in pts if p.accession)),
                                ciq_breakdown=round(c, 3))
                for q, (v, derived, pts), c in zip(row.quarters, got, per_q, strict=True)]
    missed = [(x, c) for x, c in zip(quarters, per_q, strict=True)
              if abs(c - x.value) > BREAKDOWN_SLACK_MUSD]
    if missed:
        return Decision(row, None, (
            f"the quarterly export's breakdown of the containing line us-gaap:{wider.tag} "
            f"({', '.join(wider.components)} and this row) misses the filed line by more than "
            f"{BREAKDOWN_SLACK_MUSD} $M in {len(missed)} of {len(quarters)} quarters: "
            + "; ".join(f"{c:,.1f} against {x.value:,.3f} filed ({x.end})" for x, c in missed)))
    filed_ltm = sum(x.value for x in quarters)
    accs = sorted({a for x in quarters for a in x.accessions})
    label = row.label.removesuffix(" ($M)")
    ref = (f"CIQ Financials (Quarterly)→Income Statement '{label}', four quarters to "
           f"{row.ltm_end.isoformat()}, its breakdown reconciling in every quarter to EDGAR XBRL "
           f"us-gaap:{wider.tag} as filed by {as_filed_by.isoformat()} ({', '.join(accs)})")
    apart = [f"{lab} {av:+,.1f} where the quarterly export's four quarters carry "
             + ("no figure" if qv is None else f"{qv:+,.1f}")
             for lab, (av, qv) in parts.items()
             if av is not None and (qv is None or not lq.agrees(av, qv))]
    unstated = [lab for lab, (av, _qv) in parts.items() if av is None]
    note = (("The annual export's LTM breakdown cannot be totalled: it states no LTM figure for "
             + ", ".join(unstated) + ".")
            if annual is None else
            ("The annual export reaches the same LTM total, "
             f"{annual:,.1f} against {filed_ltm:,.1f} filed, only by carrying "
             + "; ".join(apart or ["other components"])
             + ": the filed total alone cannot tell the two exports apart; the quarterly "
               "export's breakdown can be set against each quarter, and it reconciles in every one")
            if lq.agrees(annual, filed_ltm) else
            f"The annual export's LTM breakdown comes to {annual:,.1f} against {filed_ltm:,.1f} "
            "filed.")
    return Decision(row, FiledLtmFigure(
        label=row.label, ltm_end=row.ltm_end.isoformat(),
        value=Sourced.present(round(carried, 3), source_ref=ref), tag=wider.tag,
        kind="containing_line", components=list(wider.components), ciq_annual=row.ltm,
        ciq_quarterly=round(carried, 3), supports="quarterly", quarters=quarters,
        as_filed_by=as_filed_by.isoformat(), source_ref=ciq_readings_ref(row)), note=note)


def _judge(row: lq.LtmCheck, line: FiledLine, tag: str,
           got: list[tuple[float, bool, tuple[ConceptPoint, ...]]], facts: dict[str, Any], *,
           carried: float, as_filed_by: date) -> Decision:
    quarters = [FiledLtmQuarter(end=q.end.isoformat(), value=round(line.sign * v / 1e6, 3),
                                derived=derived, source_ref=_quarter_ref(pts, facts),
                                accessions=list(dict.fromkeys(
                                    p.accession for p in pts if p.accession)))
                for q, (v, derived, pts) in zip(row.quarters, got, strict=True)]
    filed = round(line.sign * sum(v for v, _d, _p in got) / 1e6, 3)
    to_annual, to_quarterly = lq.agrees(filed, row.ltm), lq.agrees(filed, carried)
    if not (to_annual or to_quarterly):
        return Decision(row, None, (
            f"the filed us-gaap:{tag} over the four quarters, {filed:,.1f}, reproduces neither CIQ "
            f"reading ({row.ltm:,.1f} annual, {carried:,.1f} quarterly; band "
            f"{lq.TOLERANCE:.0%} or {lq.PRINT_SLACK_MUSD} $M), so it is not shown to be the same "
            "item"))
    supports: Supports = ("both" if to_annual and to_quarterly
                          else "annual" if to_annual else "quarterly")
    accs = sorted({a for x in quarters for a in x.accessions})
    ref = (f"EDGAR XBRL us-gaap:{tag}, four quarters to {row.ltm_end.isoformat()} as filed by "
           f"{as_filed_by.isoformat()} ({', '.join(accs)})")
    return Decision(row, FiledLtmFigure(
        label=row.label, ltm_end=row.ltm_end.isoformat(),
        value=Sourced.present(filed, source_ref=ref), tag=tag, ciq_annual=row.ltm,
        ciq_quarterly=round(carried, 3), supports=supports, quarters=quarters,
        as_filed_by=as_filed_by.isoformat(), source_ref=ciq_readings_ref(row)))


def apply(mech: MechanicalLayer, figures: list[FiledLtmFigure]) -> MechanicalLayer:
    """``mech`` with each figure in its row's LTM cell, the table's source naming the filed cells,
    and the figures beside the table (`financial_summary.filed_ltm`). Raises when a figure has no
    LTM cell to land in — a decided figure the page cannot show is never dropped silently."""
    fs = mech.financial_summary
    ann = fs.annual if fs is not None else None
    table = ann.value if ann is not None else None
    if not figures:
        return mech
    if fs is None or ann is None or table is None:
        raise ValueError("a filed figure was decided for a page with no annual summary")
    cols = [str(c).strip().upper() for c in table.columns]
    if cols.count("LTM") != 1:
        raise ValueError(f"the annual summary has {cols.count('LTM')} LTM columns, not one")
    col = cols.index("LTM")
    by_label = {f.label: f for f in figures}
    rows, landed = [], set()
    for r in table.rows:
        f = by_label.get(r.label)
        if f is None or f.value.value is None:
            rows.append(r)
            continue
        values, cells = list(r.values), list(r.cells)
        if col >= len(values) or col >= len(cells):
            raise ValueError(f"{r.label}: no LTM cell to state the filed figure in")
        values[col], cells[col] = f.value.value, _fmt_m(f.value.value)
        rows.append(r.model_copy(update={"values": values, "cells": cells}))
        landed.add(r.label)
    if missing := sorted(set(by_label) - landed):
        raise ValueError(f"filed figure(s) for row(s) the annual summary does not carry: {missing}")
    src = (ann.source_ref or "") + "".join(
        f"; {f.label} LTM: {f.value.source_ref} — CIQ's two exports disagreeing" for f in figures)
    new_ann = Sourced.present(table.model_copy(update={"rows": rows}), source_ref=src,
                              note=ann.note)
    return mech.model_copy(update={"financial_summary": fs.model_copy(update={
        "annual": new_ann, "filed_ltm": list(figures)})})


def refusal_detail(decisions: list[Decision]) -> dict[str, str]:
    """{row label: why the filing could not decide} — what the refusal adds per row."""
    return {d.row.label: d.reason or "" for d in decisions if d.figure is None}
