"""The date a cover-page share count was counted, read from the filing's own cover sentence.

A COUNT DATED AFTER ITS OWN FILING IS A TAGGING SLIP (audit X1(a), operator ruling 2026-10-30:
"Yes, cross-check"). VRRM's 10-Q filed 2026-08-05 tags its cover count 2026-08-31, while its cover
says "As of August 3, 2026, there were 151,982,804 shares"; 107 of the 91,485 share points in the
2,253 cached companyfacts end after their own filing. The one-sided age check passed every one —
a future date is never "too old" — so THM served a 2023 count as fresh, tagged 2033.

So such a count is DATED from the cover sentence, by an anchored parse (never a model): the
sentence must carry the tagged value itself, and exactly one date introduced by "as of", "as at",
"at" or "on". A cover that cannot be read dates the count at its filing day, an UPPER bound, which
every reader prints as "filed <date>" — never as the count's own date. And the VALUE is checked
against another count in the same filing (:func:`cross_check`); a disagreement past
:data:`CROSS_CHECK_TOL` makes the count UNKNOWN, naming both figures — never one picked."""
from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from typing import Any

from vinci.edgar.concepts import ConceptPoint, points_for_tag

_MONTHS = {m: i for i, m in enumerate(
    ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"), 1)}
_MONTH = (r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?"
          r"|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?")
#: "as of August 3, 2026" — the one date shape a cover sentence introduces a count with
_DATED = re.compile(rf"\b(?:as\s+of|as\s+at|at|on)\s+({_MONTH})\s+(\d{{1,2}}),?\s+(\d{{4}})\b",
                    re.IGNORECASE)
#: a sentence ends at a period after a lower-case letter, digit or ")" that a capital follows —
#: so "Aug. 3" and "Rule 12b-2 of the Exchange Act. YES" read as one would
_SENTENCE_END = re.compile(r"(?<=[a-z0-9)])\.\s+(?=[A-Z])")
#: how far either side of the count its date may sit, inside the count's own sentence
_REACH = 300

#: an inline-XBRL filing opens with its hidden facts, which no reader sees and which can run to
#: hundreds of thousands of characters (Farmers National Banc's 10-K: to character 756,469)
_IX_HEADER = re.compile(r"<ix:header>.*?</ix:header>", re.IGNORECASE | re.DOTALL)
#: how much of a filing's visible HTML is read for its cover sentence — the cover leads it
COVER_HEAD_CHARS = 400_000


def cover_head(html: str) -> str:
    """The opening of a filing's VISIBLE HTML, where its cover sentence is: the hidden inline-XBRL
    header dropped first, so a long one cannot push the cover past the cut."""
    return _IX_HEADER.sub(" ", html, count=1)[:COVER_HEAD_CHARS]


#: The cover-vs-filing tolerance, set by FACE VALIDITY and never on an outcome. Between a filing's
#: balance-sheet date and its cover date a company buys back or issues for a few weeks; measured
#: over every cover count in the cache with a same-filing balance-sheet count (66,950, 2026-10-30),
#: the gap's median is 0.05%, p75 0.36%, p90 2.07%, p95 8.72%. 5% admits a month or two of
#: ordinary buybacks or issuance (93.5% of those cover counts sit within it) and refuses what a
#: second share class or a unit slip produces — tens of percent or more.
CROSS_CHECK_TOL = 0.05


def cover_date(text: str, value: float) -> date | None:
    """The date the cover sentence carrying ``value`` counts it at, or None when no sentence does.

    ``text`` is the filing's text (tags stripped). The count is found as the cover prints it
    (``151,982,804``), at its FIRST occurrence — the cover leads the document — and its sentence,
    within :data:`_REACH` characters either side, must hold exactly one introduced date. Two
    dates, none, or a later occurrence are None, never a guess.

    THE FIRST OCCURRENCE ONLY. Reading on to the next one took a date from the financial
    statements whenever the cover's own was unreadable: Whitestone's cover prints "As o f May 4,
    2026" and its balance sheet's 2026-03-31 was read instead (measured over 3,450 cached covers,
    2026-10-30)."""
    if value <= 0 or value != int(value):
        return None
    needle = f"{int(value):,}"
    m = re.search(rf"(?<![\d,]){re.escape(needle)}(?![\d,])", text)
    if m is None:
        return None
    lo = max(0, m.start() - _REACH)
    hi = min(len(text), m.end() + _REACH)
    before = list(_SENTENCE_END.finditer(text, lo, m.start()))
    start = before[-1].end() if before else lo
    after = _SENTENCE_END.search(text, m.end(), hi)
    end = after.start() if after else hi
    dates = {d for d in (_parse(x) for x in _DATED.finditer(text, start, end)) if d}
    return dates.pop() if len(dates) == 1 else None


#: How long before its filing a cover can count its shares, by FACE VALIDITY: "the latest
#: practicable date" sits days before a 10-K or 10-Q (median 7 and 6 days; 98.4% and 99.4% within
#: 90, over every correctly-dated cover count in the cache, 2026-10-30), while a 20-F or 40-F counts
#: at its fiscal year end (median 91 and 79 days; 96.3% and 99.2% within 180). A date further back
#: is not the count's: it is the market-value date a cover table or an unpunctuated cover runs
#: into (Hawaiian Electric's and CVB's 10-Ks read June 30, 2025 for counts filed in February).
MAX_LEAD_DAYS = 90
MAX_LEAD_DAYS_ANNUAL_FPI = 180


def max_lead_days(form: str | None) -> int:
    """The furthest before its filing a ``form``'s cover may count its shares."""
    return (MAX_LEAD_DAYS_ANNUAL_FPI if (form or "").removesuffix("/A") in ("20-F", "40-F")
            else MAX_LEAD_DAYS)


def _parse(m: re.Match[str]) -> date | None:
    month = _MONTHS.get(m.group(1)[:3].lower())
    try:
        return date(int(m.group(3)), month, int(m.group(2))) if month else None
    except ValueError:  # "February 30" is no date
        return None


@dataclass(frozen=True)
class CrossCheck:
    """One count held against another in the same filing (or the previous cover)."""

    value: float
    other: float
    other_label: str  # what the other count is and where it was read

    @property
    def gap(self) -> float:
        return self.value / self.other - 1.0

    @property
    def agrees(self) -> bool:
        return abs(self.gap) <= CROSS_CHECK_TOL


#: a weighted average over at most this many days is a QUARTER's — the cross-check's second rung
_QUARTER_MAX_DAYS = 100


def cross_check(point: ConceptPoint, series: list[ConceptPoint],
                facts: dict[str, Any]) -> CrossCheck | None:
    """``point`` held against the nearest other count, in the ruling's order: the same filing's
    balance-sheet ``CommonStockSharesOutstanding`` (its latest instant), else the same filing's
    quarter diluted weighted average, else the previous correctly-dated count in ``series``. None
    when there is none. A reference dated after its own filing is never one."""
    acc = point.accession
    bs = [q for q in points_for_tag(facts, "CommonStockSharesOutstanding")
          if acc and q.accession == acc and q.is_instant and q.value and q.period_end <= q.filed]
    if bs:
        ref = max(bs, key=lambda q: (q.period_end, q.filed))
        return CrossCheck(point.value, ref.value,
                          f"the same filing's balance-sheet count at {ref.period_end}")
    wavg = [q for q in points_for_tag(facts, "WeightedAverageNumberOfDilutedSharesOutstanding")
            if acc and q.accession == acc and q.value and q.period_start is not None
            and (q.period_end - q.period_start).days <= _QUARTER_MAX_DAYS]
    if wavg:
        ref = max(wavg, key=lambda q: (q.period_end, q.filed))
        return CrossCheck(point.value, ref.value, f"the same filing's diluted weighted average "
                                                  f"for {ref.period_start}..{ref.period_end}")
    prev = [q for q in series
            if q.value and q.period_end <= q.filed and q.filed < point.filed]
    if prev:
        ref = max(prev, key=lambda q: (q.period_end, q.filed))
        return CrossCheck(point.value, ref.value,
                          f"the previous cover count at {ref.period_end} ({ref.accession})")
    return None


@dataclass(frozen=True)
class DatedCount:
    """One share count as a reader uses it. ``point.period_end`` is the date it is READ at."""

    point: ConceptPoint
    tagged: date  # the date the filer tagged — the read date unless it fell after the filing
    bound: bool = False  # dated at its filing day: the count's own date is unknown, no later
    refused: str | None = None  # the value disagrees with its own filing: the count is UNKNOWN
    flags: tuple[str, ...] = ()  # the QA flags its correction raised, for a page that reads it

    @property
    def when(self) -> str:
        """The date as a page prints it — a filing-day bound says so."""
        return f"filed {self.point.period_end}" if self.bound else str(self.point.period_end)


def date_counts(series: list[ConceptPoint], facts: dict[str, Any], *,
                read: Callable[[ConceptPoint], str | None]) -> list[DatedCount]:
    """Every count in ``series``, each dated as it can be read, carrying its correction's flags.

    A count dated on or before its filing is kept as tagged. One dated AFTER it is dated from its
    cover sentence (``read`` returns the filing's text, or None when it cannot be had), else at its
    filing day as an upper bound; its value is then cross-checked (:func:`cross_check`) and a
    disagreement past :data:`CROSS_CHECK_TOL` refuses it. Each correction flags the tagged date,
    the date read (or the bound) and the accession; a refusal flags both figures."""
    out: list[DatedCount] = []
    for p in series:
        if p.period_end <= p.filed:
            out.append(DatedCount(p, p.period_end))
            continue
        text = read(p)
        stated = cover_date(text, p.value) if text else None
        # a cover counts before it is filed, and not further back than its form allows
        on = (stated if stated is not None
              and 0 <= (p.filed - stated).days <= max_lead_days(p.form) else None)
        head = (f"share count: {p.accession} tags {p.value:,.0f} shares at {p.period_end}, after "
                f"its own filing on {p.filed} —")
        why = ("its cover sentence could not be read" if stated is None else
               f"its cover sentence's date {stated} is not one a {p.form or 'filing'} cover counts "
               f"at (within {max_lead_days(p.form)} days before its filing)")
        flags = [f"{head} its cover counts them as of {on}; dated {on}" if on else
                 f"{head} {why}; dated no later than its filing day (filed {p.filed})"]
        check = cross_check(p, series, facts)
        refused = None
        if check is None:
            flags.append(f"{head} no other count in the filing or before it to cross-check it")
        elif not check.agrees:
            refused = (f"{p.accession}'s count {p.value:,.0f} and {check.other_label} "
                       f"{check.other:,.0f} differ by {check.gap:+.1%}, past the "
                       f"{CROSS_CHECK_TOL:.0%} cross-check — the count is UNKNOWN")
            flags.append(f"share count UNKNOWN: {refused}")
        out.append(DatedCount(p.model_copy(update={"period_end": on or p.filed}), p.period_end,
                              bound=on is None, refused=refused, flags=tuple(flags)))
    return out
