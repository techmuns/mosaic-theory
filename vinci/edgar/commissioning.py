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
#: The in-service TOTAL row, so `like_for_like` has a denominator the filing itself states rather
#: than one this module sums. Reading the stated total means a member this parser does not know
#: about cannot silently drop out of the denominator.
_IN_SERVICE_TOTAL = "property and equipment, in service"


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
    #: Every in-service member summed — technical infrastructure PLUS office space PLUS corporate.
    #: Carried because it is the only denominator that is like-for-like with the numerator.
    in_service_total: float | None = None

    @property
    def ratio(self) -> float:
        """THE PLAN'S RATIO: not-yet-in-service over the TECHNICAL-INFRASTRUCTURE member alone.

        THE SCOPES DO NOT MATCH, and calling this "not earning per unit earning" — as an earlier
        draft of this module did — is wrong. `Assets not yet in service` is ONE member covering
        EVERY asset type; `Technical infrastructure` is one of three in-service members
        (247,177 + 50,635 + 6,498 = 304,310). So the numerator includes office and corporate
        construction the denominator excludes, and the quotient is not a commissioning rate.

        It is kept, and kept FIRST, because it is the number the monitoring plan states and tracks
        (38.6% -> 49.7%) and changing it silently would break the operator's own series. What is
        fixed is the description: this is not-yet-in-service EXPRESSED AGAINST the technical
        infrastructure base — a spend-intensity measure, and a fair one given technical
        infrastructure is ~81% of in-service assets and where the AI capital goes. `like_for_like`
        below is the coherent comparison, and the gap between them is real: 49.7% vs 40.4%.
        """
        return self.not_yet_in_service / self.in_service

    @property
    def like_for_like(self) -> float | None:
        """Not-yet-in-service over ALL in-service assets — same scope on both sides.

        None when the note does not state every in-service member, because a partial sum would be
        a denominator nobody could reconcile to the filing.
        """
        if self.in_service_total is None:
            return None
        return self.not_yet_in_service / self.in_service_total


def _periods_from(cells: list[str]) -> list[str]:
    """The dated column headers in this row, POSITIONALLY ALIGNED with a value row — or [].

    THE EMPTIES ARE KEPT, and that is the whole point. Value rows read `cells[1:]` with blanks
    intact so a missing figure holds its own column; a header read that DROPS blanks pairs against
    them one place out, and a single spacer cell relabels every figure with the wrong period —
    silently, because both lists still zip. Confirmed on this note by inserting one spacer: the
    June figures came back stamped December and the June column vanished. Same defect the segment
    parser carried, in the file written to avoid it.
    """
    trailing = cells[1:] if cells and not re.match(r"[A-Z][a-z]{2}\. \d", cells[0]) else cells
    dated = [c for c in trailing if c]
    if not dated or not all(re.match(r"[A-Z][a-z]{2}\. \d", c) for c in dated):
        return []
    return trailing


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
        fname, short = _pick_report(summary, topic=_PPE_REPORT, refine=_ANY,
                                     what="property-and-equipment")
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
            # A FILER REPORTING IN WHOLE DOLLARS HAS NO "$ in" CAPTION, so period capture cannot
            # live inside this branch: it would never run, the note would yield no figures, and
            # the refusal would blame the note for stating no periods when the real fault is a
            # missing scale caption. The period scan below runs for every row.
            # THE CAPTION MAY CARRY THE PERIODS TOO, and in this note it does. The segment report
            # puts the scale and the dates on separate rows; the PP&E note puts them on one, so a
            # reader that consumes the caption and moves on discards every column header and then
            # finds no figures at all — which is what this refused with, correctly but uselessly.
            # Two reports in one filing, two shapes: neither is assumable from the other.
            _maybe = _periods_from(cells)
            if _maybe:
                periods = _maybe
            continue
        if not periods:
            _maybe = _periods_from(cells)
            if _maybe:
                periods = _maybe
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
            if low in (_NOT_IN_SERVICE, _IN_SERVICE, _IN_SERVICE_TOTAL):
                heading = low
            elif periods and not low.startswith("("):
                heading = ""                     # any other member ends the one we were under
            continue
        if not (heading and periods) or head.lower() != _GROSS:
            continue
        values = [_number(c) for c in cells[1:]]
        # COLUMN COUNTS MUST AGREE, and a mismatch is REFUSED rather than zipped through. Keeping
        # blanks on both sides is not enough on its own: a spacer cell present in the header and
        # absent from the value rows still pairs them one place out, and both lists still zip
        # happily — June's figure lands under December, December's under an unnamed column, and
        # every total still reconciles inside whichever column it landed in. There is no way to
        # tell which side gained the cell, so the honest answer is to stop.
        if len(values) != len(periods):
            raise CommissioningUnavailableError(
                f"{fname}: the row '{head}' has {len(values)} value columns against "
                f"{len(periods)} period headers ({periods}). A figure cannot be attributed to a "
                f"period when the columns do not line up, and guessing which side gained a cell "
                f"would relabel every figure in the note.")
        for period, val in zip(periods, values, strict=True):
            if val is not None and period:
                found.setdefault(period, {})[heading] = val

    out = [Commissioning(period=p, not_yet_in_service=v[_NOT_IN_SERVICE],
                         in_service=v[_IN_SERVICE], unit=unit, source_ref=src,
                         in_service_total=v.get(_IN_SERVICE_TOTAL))
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
