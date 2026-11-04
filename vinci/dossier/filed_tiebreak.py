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

`NonoperatingIncomeExpense` IS NOT MAPPED. It is the filer's whole "other income (expense)" line,
and CIQ always splits that line above its unusual-items block (interest and investment income,
currency gains, other non-operating). An unusual-items row can therefore never be the whole line.
NFLX is the measured case. Its filed line for Q1 2026 is 2,852.166M (10-Q 0001065280-26-000138),
which CIQ's own Q1 rows reproduce exactly: interest income 70.0, FX -8.3, other -9.5 and the merger
row 2,800.0. Over the LTM to 2026-09-30 the line reads 2,992.3, which includes about 190M of
interest and currency. Stating it as the merger row would state a different item. The line
supports the quarterly export's SIGN, and NFLX stays refused for the operator's call.

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
on whether the filer tags the item in XBRL. CELH tags its charge as `RestructuringCharges`; NFLX's
merger fee sits inside a containing line, and WAT's merger costs and NKE's restructuring are tagged
under no mapped concept in the window. That selection decides only whether a page can be BUILT on a
verified figure. A name it cannot clear is refused exactly as before, so the selection can only ever
leave a name where it was.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from vinci.dossier import ltm_quarters as lq
from vinci.dossier.ciq_sheets import _fmt_m
from vinci.dossier.schemas import (
    FiledLtmFigure,
    FiledLtmQuarter,
    MechanicalLayer,
    Sourced,
    Supports,
)
from vinci.edgar.concepts import ConceptPoint, facts_as_of, filed_at, points_for_tag

#: A filed period ends on CIQ's quarter end, or within a week of it (a 52/53-week filer's quarter
#: lands a few days off a calendar date, and CIQ names it by its fiscal end).
SAME_END_DAYS = 7
#: A quarter is 80-100 days — a 13-week quarter, or a 14-week one in a 53-week year.
QUARTER_DAYS = (80, 100)


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
class Decision:
    """The filing's answer for one refused row: a figure, or why the filing cannot decide."""

    row: lq.LtmCheck
    figure: FiledLtmFigure | None
    reason: str | None = None

    def caveat(self) -> str:
        """The main-body caveat: what the page states, where it was filed, and what CIQ said."""
        f = self.figure
        if f is None or f.value.value is None:
            raise ValueError("no filed figure — a refused row has no caveat, it has a refusal")
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
    points, or None when the filer stated nothing it can be read from."""
    near = [p for p in points if p.period_start is not None
            and abs((p.period_end - end).days) <= SAME_END_DAYS]
    three = [p for p in near if QUARTER_DAYS[0] <= _days(p) <= QUARTER_DAYS[1]]
    if three:
        p = max(three, key=_latest)
        return p.value, False, (p,)
    for p in sorted((p for p in near if _days(p) > QUARTER_DAYS[1]), key=_latest,
                    reverse=True):
        shorter = [x for x in points if x.period_start == p.period_start
                   and QUARTER_DAYS[0] <= (p.period_end - x.period_end).days <= QUARTER_DAYS[1]]
        if shorter:
            q = max(shorter, key=_latest)
            return p.value - q.value, True, (p, q)
    return None


def _quarter_ref(pts: tuple[ConceptPoint, ...], facts: dict[str, Any]) -> str:
    if len(pts) == 1:
        return filed_at(pts[0], facts)
    return f"{filed_at(pts[0], facts)} − {filed_at(pts[1], facts)}"


def decide(row: lq.LtmCheck, facts: dict[str, Any], *, as_filed_by: date) -> Decision:
    """The filing's answer for one row ``ltm_quarters`` refuses. ``facts`` is the whole
    companyfacts blob; it is cut at ``as_filed_by`` here, before anything is read."""
    if row.outcome != "differ" or row.carried is None or not row.quarters:
        return Decision(row, None, "the filing decides between two CIQ readings, and the "
                                   "quarterly export gives no second reading here")
    line = MAPPING.get(row.label)
    if line is None:
        return Decision(row, None, f"no reviewed mapping from the CIQ row {row.label!r} to a filed "
                                   "concept (`filed_tiebreak.MAPPING`)")
    cut = facts_as_of(facts, as_filed_by)
    misses: list[str] = []
    for tag in line.tags:
        pts = points_for_tag(cut, tag)
        got = [filed_quarter(pts, q.end) for q in row.quarters]
        if any(g is None for g in got):
            gone = ", ".join(q.end.isoformat() for q, g in zip(row.quarters, got, strict=True)
                             if g is None)
            misses.append(f"us-gaap:{tag} " + (f"states no quarter to {gone}" if pts else
                                                "carries no fact")
                          + f" as filed by {as_filed_by}")
            continue
        return _judge(row, line, tag, [g for g in got if g is not None], cut,
                      carried=row.carried, as_filed_by=as_filed_by)
    return Decision(row, None, "no filed figure for every quarter — " + "; ".join(misses))


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
        as_filed_by=as_filed_by.isoformat()))


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
