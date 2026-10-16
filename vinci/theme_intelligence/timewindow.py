"""Calendar windows for the 2-4-quarter test — read from a claim's stated period, never guessed.

"Near term" is a claim about TIME, so it is tested against time. `window_of` reads the calendar
window a period string names ("NTM", "4Q26", "2H 2026", "2025-2031", "FY27", "September 2026",
"next year") relative to the as-of date, and `timing_of` sorts one claim into

  near_term   a forecast / scheduled event whose window ends within the next four quarters of the
              as-of (config NEAR_TERM_*) — the next 2-4 quarters;
  straddling  a window that runs past them with MOST of it inside them (an undifferentiated "2027"
              in October 2026) — not near-term evidence, and not longer-term only;
  long_range  a forecast / event whose window reaches past that ("a 2025-2031 CAGR") — a forecast
              does NOT qualify merely because it is a forecast — or an opinion naming such a
              horizon ("unlikely to clear before 2030"); a view is never near-term evidence;
  current     a MEASURED observation dated at most one quarter before the as-of
              (config CURRENT_OBSERVATION_DAYS) — the condition exists now;
  historical  a measured observation older than that, or a forecast window already past;
  undated     no readable window (an opinion, or a period this reader cannot place) — never
              assumed near.

A fiscal year is read as the calendar year it is named for, and the note says so (fiscal
calendars differ by issuer). A fiscal QUARTER is not placed at all: "Q1 FY27" is NVIDIA's
February-April 2026 and a calendar issuer's January-March 2027, so read as either it can be a year
wrong. "Since X" runs from X to the source's own date. A four-digit amount ("$2050 per ounce") is
not a year. Nothing here reads prices or returns.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta

from vinci.theme_intelligence.config import (
    CURRENT_OBSERVATION_DAYS,
    NEAR_TERM_END_DAYS,
    NEAR_TERM_START_DAYS,
)
from vinci.theme_intelligence.schemas import Claim, ClaimKind, Epistemic


@dataclass(frozen=True)
class Window:
    start: date
    end: date
    basis: str  # the text the window was read from, and how
    #: "since X": a change accumulated from X to the SOURCE'S date (`window_of(source_date=)`)
    to_date: bool = False

    def __str__(self) -> str:
        return f"{self.start.isoformat()}..{self.end.isoformat()} ({self.basis})"


_MONTHS = {m: i for i, ms in enumerate(
    [("jan", "january"), ("feb", "february"), ("mar", "march"), ("apr", "april"), ("may",),
     ("jun", "june"), ("jul", "july"), ("aug", "august"), ("sep", "sept", "september"),
     ("oct", "october"), ("nov", "november"), ("dec", "december")], start=1) for m in ms}
_ORD = {"first": 1, "second": 2, "third": 3, "fourth": 4, "1st": 1, "2nd": 2, "3rd": 3, "4th": 4}
_COUNT = {"two": 2, "three": 3, "four": 4, "2": 2, "3": 3, "4": 4}
_MONTHS_N = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
             "nine": 9, "ten": 10, "eleven": 11, "eighteen": 18, "twenty-four": 24}
_MONTHS_N_WORD = "|".join(sorted(_MONTHS_N, key=len, reverse=True))
#: a fiscal quarter — not placed (see the module note)
FISCAL_QUARTER = re.compile(r"\b(?:q[1-4]\s?fy\s?'?\d{2,4}|[1-4]q\s?fy\s?'?\d{2,4}|"
                            r"fy\s?'?\d{2,4}\s?(?:q[1-4]|[1-4]q))\b", re.I)
#: a four-digit number that is an AMOUNT, not a year: after a currency sign, or before a unit —
#: "per" / "/" only before a unit ("$2050 per ounce", "2050/oz"), so "2025/26" and "2030 per the
#: IEA" stay years
_PER_UNIT = r"(?:ounce|oz|barrel|bbl|tonne|ton|share|unit|kg|lb|mwh|kwh|gw|mw|t)\b"
_AMOUNT_AFTER = (rf"(?!\s*(?:%|bn\b|billion|million|mn\b|tonnes?\b|oz\b|barrels?\b|"
                 rf"per\s+{_PER_UNIT}|/\s*{_PER_UNIT}))")
_YEARS = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
          "nine": 9, "ten": 10, "fifteen": 15, "twenty": 20}
_YEARS_WORD = "|".join(_YEARS)
_YY = r"'?(\d{4}|\d{2})"


def _years(tok: str) -> int:
    return _YEARS[tok] if tok in _YEARS else int(tok)
_MONTH_RE = "|".join(sorted(_MONTHS, key=len, reverse=True))
#: a NEXT-TWELVE-MONTHS figure (an NTM margin, a forward-12-month estimate) — one definition for
#: `window_of` and `timing_of`
_NTM_WORDS = (r"ntm|next\s+(?:twelve|12)\s+months|(?:twelve|12)[- ]months?\s+(?:forward|ahead)|"
              r"forward\s+(?:twelve|12)[- ]months?")
NTM = re.compile(rf"\b(?:{_NTM_WORDS})\b", re.I)
#: a period this short names WHEN a figure was read ("At Feb '26"), not the window it covers
READING_DATE_DAYS = 31


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s).lower()
    return re.sub(r"[‐-―−]", "-", s)


def _year(tok: str) -> int:
    y = int(tok)
    return y + 2000 if y < 100 else y


def _year_end(y: int) -> date:
    return date(y, 12, 31)


def _quarter(q: int, y: int) -> tuple[date, date]:
    start = date(y, 3 * (q - 1) + 1, 1)
    end = (date(y + 1, 1, 1) if q == 4 else date(y, 3 * q + 1, 1)) - timedelta(days=1)
    return start, end


def _half(h: int, y: int) -> tuple[date, date]:
    return (date(y, 1, 1), date(y, 6, 30)) if h == 1 else (date(y, 7, 1), date(y, 12, 31))


def _month(m: int, y: int) -> tuple[date, date]:
    end = (date(y + 1, 1, 1) if m == 12 else date(y, m + 1, 1)) - timedelta(days=1)
    return date(y, m, 1), end


def window_of(text: str | None, ref: date, *, source_date: date | None = None) -> Window | None:
    """The calendar window `text` names, relative to `ref`; None when it names none readable.
    Several windows in one text are unioned (earliest start, latest end). A "since X" part ends at
    `source_date` (the source's own date), else at `ref` — only that part: a later window in the
    same text keeps its own end."""
    if not text:
        return None
    work = _norm(text)
    found: list[tuple[date, date, str]] = []
    since = False
    work = FISCAL_QUARTER.sub(lambda m: " " * len(m.group(0)), work)  # never placed

    def take(pattern: str, make: Callable[[re.Match[str]], tuple[date, date] | None]) -> None:
        nonlocal work
        for m in list(re.finditer(pattern, work)):
            got = make(m)
            if got is None:
                continue
            found.append((got[0], got[1], m.group(0).strip()))
            work = work[:m.start()] + " " * (m.end() - m.start()) + work[m.end():]

    def _since(m: re.Match[str]) -> tuple[date, date] | None:
        nonlocal since
        y = int(m.group(3))
        start = (_month(_MONTHS[m.group(2)], y)[0] if m.group(2) else
                 date(y, 7, 1) if (m.group(1) or "").startswith("mid") else
                 date(y, 10, 1) if (m.group(1) or "").startswith("late") else date(y, 1, 1))
        if start > ref:
            return None
        since = True
        return start, (source_date if source_date is not None and start <= source_date <= ref
                       else ref)

    # "since X" runs from X to the source's date (2026-10-14: "since May 2026" was read as May
    # alone, dated its end, and called historical — 12 of 520 pilot claims)
    take(rf"\bsince\s+((?:the\s+)?(?:start|beginning)\s+of\s+|(?:early|mid|late)[- ]?)?"
         rf"(?:({_MONTH_RE})\.?\s+)?((?:19|20)\d{{2}})\b"
         rf"(?!\s*(?:-|to|through|thru|until)\b)", _since)
    take(rf"\b({_NTM_WORDS}|coming\s+year|year\s+ahead)\b",
         lambda m: (ref, ref + timedelta(days=365)))
    # N quarters are N fourths of a year: "next four quarters" is the next 12 months (92 days a
    # quarter made it 368, past the 366-day near-term bound)
    take(r"\b(?:next|coming|within(?:\s+the)?(?:\s+next)?)\s+(two|three|four|2|3|4)\s+"
         r"quarters\b",
         lambda m: (ref, ref + timedelta(days=round(365 * _COUNT[m.group(1)] / 4))))
    take(rf"\b(?:next|coming|within(?:\s+the)?(?:\s+next)?)\s+({_MONTHS_N_WORD}|\d{{1,2}})\s+"
         rf"months\b",
         lambda m: (ref, ref + timedelta(days=round(365 * int(_MONTHS_N.get(m.group(1),
                                                                          m.group(1))) / 12))))
    take(r"\b(?:next|coming)\s+quarter\b", lambda m: (ref, ref + timedelta(days=92)))
    # relative MULTI-YEAR windows, read from the source's words (observed 2026-10-12: "over the
    # next five years", "over the next decade" and "before 2030" were unread, so long-dated
    # evidence looked undated and a SKIP-3 thesis read as WATCH)
    take(rf"\b(?:next|coming|following)\s+({_YEARS_WORD}|\d{{1,2}})\s+years\b",
         lambda m: (ref, ref + timedelta(days=round(365.25 * _years(m.group(1))))))
    take(r"\b(?:next|coming)\s+decade\b", lambda m: (ref, ref + timedelta(days=3652)))
    take(r"\b(?:the\s+)?end\s+of\s+(?:the|this)\s+decade\b",
         lambda m: (ref, _year_end(ref.year // 10 * 10 + 9)))
    take(r"\binto\s+the\s+((?:19|20)\d0)s\b",
         lambda m: (ref, _year_end(int(m.group(1)) + 9)) if int(m.group(1)) + 9 >= ref.year
         else None)
    take(r"\bbefore\s+((?:19|20)\d{2})\b",
         lambda m: (ref, _year_end(int(m.group(1)) - 1)) if int(m.group(1)) - 1 >= ref.year
         else None)
    take(r"\b(?:year[- ]to[- ]date|ytd)\b", lambda m: (date(ref.year, 1, 1), ref))
    take(r"\b(?:this|current)\s+year\b", lambda m: (date(ref.year, 1, 1), _year_end(ref.year)))
    take(r"\bnext\s+year\b", lambda m: (date(ref.year + 1, 1, 1), _year_end(ref.year + 1)))
    take(rf"\b([1-4])q\s?{_YY}\b", lambda m: _quarter(int(m.group(1)), _year(m.group(2))))
    take(rf"\bq([1-4])\s?{_YY}\b", lambda m: _quarter(int(m.group(1)), _year(m.group(2))))
    take(r"\b(first|second|third|fourth|1st|2nd|3rd|4th)\s+quarter\s+(?:of\s+)?(\d{4})\b",
         lambda m: _quarter(_ORD[m.group(1)], int(m.group(2))))
    take(rf"\b([12])h\s?{_YY}\b", lambda m: _half(int(m.group(1)), _year(m.group(2))))
    take(rf"\bh([12])\s?{_YY}\b", lambda m: _half(int(m.group(1)), _year(m.group(2))))
    take(r"\b(first|second|1st|2nd)\s+half\s+(?:of\s+)?(\d{4})\b",
         lambda m: _half(_ORD[m.group(1)], int(m.group(2))))
    take(rf"\bfy\s?{_YY}\b", lambda m: (date(_year(m.group(1)), 1, 1),
                                        _year_end(_year(m.group(1)))))
    take(r"(?<![$€£¥])\b((?:19|20)\d{2})\s*(?:-|to|through|thru|until)\s*((?:19|20)?\d{2})\b"
         + _AMOUNT_AFTER, lambda m: _range(int(m.group(1)), m.group(2)))
    take(r"\b(?:by|through|thru|until)\s+(?:the\s+end\s+of\s+)?((?:19|20)\d{2})\b",
         lambda m: (ref, _year_end(int(m.group(1)))) if int(m.group(1)) >= ref.year else None)
    take(rf"\b({_MONTH_RE})\.?\s+(\d{{1,2}}),?\s+((?:19|20)\d{{2}})\b",
         lambda m: _day(m.group(1), m.group(2), m.group(3)))
    take(rf"\b({_MONTH_RE})\.?\s+((?:19|20)\d{{2}})\b",
         lambda m: _month(_MONTHS[m.group(1)], int(m.group(2))))
    take(r"(?<![$€£¥])\b((?:19|20)\d{2})\b" + _AMOUNT_AFTER,
         lambda m: (date(int(m.group(1)), 1, 1), _year_end(int(m.group(1)))))
    if not found:
        return None
    start = min(f[0] for f in found)
    end = max(f[1] for f in found)
    basis = "; ".join(dict.fromkeys(f[2] for f in found))
    if any(f[2].startswith("fy") for f in found):
        basis += " (fiscal year read as the calendar year — approximate)"
    return Window(start, end, basis, to_date=since)


def _range(a: int, b_tok: str) -> tuple[date, date] | None:
    b = int(b_tok)
    if b < 100:
        b += (a // 100) * 100
    if b < a:
        return None
    return date(a, 1, 1), _year_end(b)


def _day(mon: str, day: str, year: str) -> tuple[date, date] | None:
    try:
        d = date(int(year), _MONTHS[mon], int(day))
    except ValueError:
        return None
    return d, d


def is_near_term(w: Window, ref: date) -> bool:
    """A FORWARD window inside the next 2-4 quarters: it has not ended, it starts within
    NEAR_TERM_START_DAYS and it ends within NEAR_TERM_END_DAYS of the as-of."""
    return (w.end >= ref and w.start <= ref + timedelta(days=NEAR_TERM_START_DAYS)
            and w.end <= ref + timedelta(days=NEAR_TERM_END_DAYS))


def straddles(w: Window, ref: date) -> bool:
    """A window that runs PAST the next four quarters with MOST of it inside them — an
    undifferentiated "2027" read in October 2026 (pilot 2026-10-12: nine and a half of its twelve
    months). It is not a 2-4-quarter window, so it never shows near-term relevance; and it is not
    longer-term only, so it never makes a thesis SKIP-3 either."""
    horizon = ref + timedelta(days=NEAR_TERM_END_DAYS)
    inside = (min(w.end, horizon) - max(w.start, ref)).days + 1
    return w.end > horizon and 2 * inside > (w.end - w.start).days + 1


def ntm_window(c: Claim, w: Window | None, published: date | None) -> Window | None:
    """The window of a NEXT-TWELVE-MONTHS forecast: the twelve months after the figure was READ —
    never the run's as-of, and never the reading date's own month. 2026-10-16: "NTM net margin …
    At Feb '26" was dated as a one-month forecast window, February 2026 (the period held the
    reading date); and a period of bare "NTM" was anchored to the run's date, so the same stored
    figure moved forward on every later reassessment.

    The reading date: the claim's measurement date, else a period that names a single day or month
    (`READING_DATE_DAYS`), else the source's date. None — the window stands as read — when the
    claim names no NTM measure, when its period names a longer window of its own ("2027"), or
    when no reading date is known."""
    if not any(NTM.search(x or "") for x in (c.period, c.metric, c.quote)):
        return None
    short = w is not None and (w.end - w.start).days < READING_DATE_DAYS
    if w is not None and not short and not NTM.search(c.period or ""):
        return None  # the period names the figure's own window
    read = c.measured_as_of or (w.start if short and w is not None else None) or published
    if read is None:
        return None
    return Window(read, read + timedelta(days=365),
                  f"NTM from {read.isoformat()} — the twelve months after the figure was read")


def timing_of(c: Claim, ref: date, published: date | None) -> tuple[str, str]:
    """(near_term | straddling | long_range | current | historical | undated, a note naming the
    window)."""
    forward = c.epistemic is Epistemic.FORECAST or c.kind is ClaimKind.FORECAST
    w = window_of(c.period, ref, source_date=published)
    if w is None and (forward or c.kind is ClaimKind.EVENT):
        w = window_of(c.quote, ref, source_date=published)
    if forward and (n := ntm_window(c, w, published)) is not None:
        w = n
    if forward:
        if w is None:
            fq = FISCAL_QUARTER.search(c.period or "") or FISCAL_QUARTER.search(c.quote or "")
            if fq is not None:
                return "undated", (f"a fiscal quarter ({fq.group(0)}) — the issuer's fiscal "
                                   f"calendar is not known here, so it is not placed")
            return "undated", "forecast with no readable time window"
        if w.end < ref:
            return "historical", f"forecast window {w} has already ended"
        if is_near_term(w, ref):
            return "near_term", f"forecast window {w}"
        if straddles(w, ref):
            return "straddling", (f"forecast window {w} runs past the next 4 quarters (most of it "
                                  f"inside them) — not a 2-4-quarter window")
        return "long_range", f"forecast window {w} reaches beyond the next 4 quarters"
    if c.epistemic is Epistemic.ACTUAL:
        if any(q.startswith("stale series") for q in c.qualifiers):
            return "historical", "stale series"
        if c.kind is ClaimKind.EVENT and w is not None and w.start > ref:
            return ("near_term" if is_near_term(w, ref) else
                    "straddling" if straddles(w, ref) else "long_range",
                    f"scheduled event window {w}")
        d = c.measured_as_of or (w.end if w is not None and w.end <= ref else None) or published
        if d is None:
            return "undated", "observation with no data date"
        age = (ref - d).days
        if age < 0:
            return "undated", f"observation dated {d.isoformat()}, after the as-of"
        if age <= CURRENT_OBSERVATION_DAYS:
            return "current", f"measured {d.isoformat()} ({age} days before the as-of)"
        return "historical", f"measured {d.isoformat()} ({age} days before the as-of)"
    # an opinion / mixed view that NAMES a horizon beyond the next 4 quarters ("unlikely to clear
    # before 2030") is long-dated evidence of the thesis's timing. It never counts as near-term:
    # only a forecast, an event or a measurement can show that.
    w = w or window_of(c.quote, ref, source_date=published)
    if w is not None and w.end > ref + timedelta(days=NEAR_TERM_END_DAYS):
        return ("straddling" if straddles(w, ref) else "long_range",
                f"{c.epistemic.value} naming a window {w} beyond the next 4 quarters (a view's "
                f"horizon — never near-term evidence)")
    return "undated", f"{c.epistemic.value} — no time window"
