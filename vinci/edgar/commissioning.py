"""(monitoring plan item 2) The "built but not running" ratio, from the filing's own PP&E note.

WHAT IT ANSWERS. Alphabet is spending roughly $200bn a year; the position rests on whether that
turns into profit fast enough. This ratio is the closest thing to watching money become a
productive asset: capital that has been PAID FOR but is not yet earning, against the capital that
is. It moved 38.6% -> 49.7% in six months — money going into the ground far faster than it comes
online — and the operator's plan calls it the highest-value cheap item in the build.

WHY IT IS NOT A SCREEN NUMBER. Both inputs are line items inside the supplemental PP&E note, under
a dimensional axis (``goog_TechnicalInfrastructureMember``, ``AssetUnderConstructionMember``).
`companyfacts` carries no dimensional qualifier, so neither figure exists in the source this repo
already pulls — the same wall the segment extractor met, met again one note over.

THE RATIO IS ALPHABET-SPECIFIC AND SAYS SO. "Technical infrastructure" and "Assets not yet in
service" are Alphabet's own PP&E presentation; the plan records that peers do not tag the
equivalent lines, so this is a per-name reader in the plan's "Google-only" tier, not a fleet
metric. It refuses rather than approximating when a filing does not carry both lines.

VERIFIED against the two filings the plan cites, reproducing its figures exactly:
  * FY2025 10-K (acc …26-000018, report R70): 78,592 / 203,679 = 38.59%  ("38.6%")
  * Q2   10-Q  (acc …26-000071, report R64): 122,814 / 247,177 = 49.69%  ("49.7%")
The report NUMBER moved between those two filings, which is precisely the plan's Part 7 trap 2 —
resolution is by ShortName, never by number.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from vinci.edgar.segments import (
    _FILING_SUMMARY,
    _REPORT,
    SegmentReportUnavailableError,
    _cells,
    _number,
    _pick_report,
)

if TYPE_CHECKING:
    from vinci.netcache import CachedHttp

_PPE_REPORT = re.compile(r"property and equipment", re.I)
_ANY = re.compile(r".", re.S)          # the PP&E note needs no second filter — one (Details) report

#: The two headings the ratio is struck from, as Alphabet writes them. Matched WHOLE and
#: case-insensitively rather than by substring: "Property and equipment, in service" also contains
#: "in service", and reading that total as the denominator would understate the ratio by a third.
_NOT_IN_SERVICE = "assets not yet in service"
_IN_SERVICE = "technical infrastructure"
#: The line under each heading that carries the figure. The note states gross PP&E per member.
_GROSS = "property, plant and equipment, gross"


class CommissioningUnavailableError(RuntimeError):
    """The filing's PP&E note does not carry both lines — stated, never approximated."""


@dataclass(frozen=True)
class Commissioning:
    """One period's commissioning state, with the arithmetic left visible.

    ``ratio`` is not rounded and not formatted: a consumer that wants "49.7%" formats it, and one
    that wants to compare periods needs the full precision. The two components are carried beside
    it so the number can be re-derived by hand from the filing, which is the only way a reader
    checks it.
    """

    period: str
    not_yet_in_service: float
    in_service: float
    unit: str
    source_ref: str

    @property
    def ratio(self) -> float:
        """Capital paid for but not yet earning, per unit of capital that is."""
        return self.not_yet_in_service / self.in_service


def commissioning(http: CachedHttp, cik: str, accession: str) -> list[Commissioning]:
    """Every period the filing's PP&E note states both lines for, newest first.

    A 10-Q states the current period AND the prior year-end, so one fetch yields the move as well
    as the level — which is what the plan actually watches ("jumped 38.6% -> 49.7% in six months").

    REFUSES A HALF-ANSWER. A filing carrying one line and not the other yields nothing rather than
    a ratio against a substituted denominator: the whole point of the number is that both sides
    come from the same note on the same date.
    """
    cik_n = str(int(cik))
    acc = accession.replace("-", "")
    summary = http.get_text(_FILING_SUMMARY.format(cik=cik_n, acc=acc), ttl_seconds=None)
    try:
        fname, short = _pick_report(summary, topic=_PPE_REPORT, refine=_ANY)
    except SegmentReportUnavailableError as exc:
        raise CommissioningUnavailableError(
            f"no property-and-equipment (Details) report in {accession}: {exc}") from exc
    doc = http.get_text(_REPORT.format(cik=cik_n, acc=acc, fname=fname), ttl_seconds=None)

    src = f"EDGAR {accession} {fname} — {short}"
    unit, heading = "", ""
    periods: list[str] = []
    found: dict[str, dict[str, float]] = {}
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", doc, re.S):
        cells = _cells(tr)
        if not any(cells):
            continue
        if not unit and "$ in" in cells[0]:
            m = re.search(r"\$ in (\w+)", cells[0])
            unit = f"${m.group(1)}" if m else ""
            # THE CAPTION MAY CARRY THE PERIODS TOO, and in this note it does. The segment report
            # puts the scale and the dates on separate rows; the PP&E note puts them on one, so a
            # reader that consumes the caption and moves on discards every column header and then
            # finds no figures at all — which is what this refused with, correctly but uselessly.
            # Two reports in one filing, two shapes: neither is assumable from the other.
            trailing = [c for c in cells[1:] if c]
            if trailing and all(re.match(r"[A-Z][a-z]{2}\. \d", c) for c in trailing):
                periods = trailing
            continue
        dated = [c for c in cells if c]
        if (not periods and dated
                and all(re.match(r"[A-Z][a-z]{2}\. \d", c) for c in dated)):
            periods = dated
            continue
        head = cells[0]
        if len([c for c in cells if c]) == 1:
            low = head.lower()
            # WHOLE-HEADING MATCH: "Property and equipment, in service" also contains "in service",
            # and reading its total as the denominator understates the ratio by about a third.
            if low.endswith("[abstract]"):
                # STRUCTURAL, NOT A HEADING. The renderer puts an "[Abstract]" row between a
                # member heading and its figures; treating it as a new heading clears the one just
                # set, and every figure below is then dropped for want of a member. The refusal
                # that produced was correct and useless — "no period states both lines" when the
                # note plainly states both.
                continue
            if low in (_NOT_IN_SERVICE, _IN_SERVICE):
                heading = low
            elif periods and not low.startswith("("):
                heading = ""                     # any other member ends the one we were under
            continue
        if not (heading and periods) or head.lower() != _GROSS:
            continue
        for period, val in zip(periods, [_number(c) for c in cells[1:]][:len(periods)],
                               strict=False):
            if val is not None:
                found.setdefault(period, {})[heading] = val

    out = [Commissioning(period=p, not_yet_in_service=v[_NOT_IN_SERVICE],
                         in_service=v[_IN_SERVICE], unit=unit, source_ref=src)
           for p, v in found.items() if _NOT_IN_SERVICE in v and _IN_SERVICE in v]
    if not out:
        raise CommissioningUnavailableError(
            f"{fname} carries no period stating BOTH '{_NOT_IN_SERVICE}' and '{_IN_SERVICE}' — a "
            f"ratio struck against a substituted denominator would not be the plan's metric, so "
            f"none is returned. Found headings: {sorted({h for v in found.values() for h in v})}")
    if not unit:
        raise CommissioningUnavailableError(
            f"{fname} states no scale, so both figures are unitless — the ratio survives that but "
            f"the levels beside it would not, and they are what a reader checks")
    return out
