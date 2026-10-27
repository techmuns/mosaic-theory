"""(2026-10-27) DEBT MATURITIES AS THE FILINGS STATE THEM — a deterministic reader, and the check of
CIQ's capital-structure panel against it.

WHY. CIQ's panel lags refinancings, and nothing compared a page's maturities with the filings.
VRRM's page printed "2021 Term Loan Due 2028 … 2028-03-24" — in the instrument table, the catalyst
calendar, the liquidity line and a synthesis key-unknown — while its own covenant pointers cited
the 8-K (0001193125-25-242530) that refinanced that loan into one maturing 2032-10-15. The evidence
was linked; its date was never read.

ANCHORED, NEVER AN LLM. The reader is a sentence grammar over the normalized filing text
(`vinci.graph.filings.normalize_text`): an instrument noun, a maturity verb, a stated date. It
reads three shapes the corpus holds, measured on the 27 committed pages' filings before any rule
was written:

* a STATEMENT — "the ABL Facility … matures on October 17, 2030", "the maturity date of the
  Continued Term Loan Facility is December 27, 2026", "ABL Credit Facility due 2031";
* a TRANSITION — "an extension of the maturity date from April 26, 2028, to May 14, 2031",
  "refinance the existing … term loans … with a new … term loan … maturing on October 15, 2032".
  The old date is SUPERSEDED, the new one current;
* a PRIOR facility — "The Prior 364-Day Credit Agreement would have expired on March 6, 2026",
  "the Existing ABL Credit Agreement … which provided for … a maturity date of December 20, 2026".
  Superseded.

A SPRINGING maturity is read where the filing states one ("subject to an earlier maturity date of
91 days prior to the April 15, 2029 maturity date of … 5.50% Senior Notes due 2029 …"): kept
verbatim, and dated only when the filing fixes the date (N days before a stated date).

THE TRAP THE CORPUS SET. VRRM's 10-Q states BOTH "The 2021 Term Loan had an aggregate borrowing of
$900.0 million, maturing on March 24, 2028" — history, and CIQ's exact date — AND the refinancing
into 2032-10-15. A reader that took the first term-loan date it met would AGREE with the stale
panel. So agreement needs more than a shared date: the filing's set of current maturities for the
class must equal the page's (`compare`), and a refinancing that leaves exactly one earlier date
beside its new one supersedes it.

FAIL LOUD, NEVER GUESS. A filing that states nothing readable for a class decides nothing; one whose
statements cannot be paired with the page's instruments one-to-one is `not_run` with the reason.
A difference is called only where the pairing is FORCED — one instrument against one current date.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta

from vinci.dossier.schemas import (
    CHECK_DIFFER,
    CHECK_NOT_RUN,
    MaturityCheck,
    MaturityCheckRow,
    MaturitySource,
    SpringingMaturity,
)

#: Instrument classes. ``FACILITY`` is a generic noun ("Credit Agreement", "Credit Facilities") —
#: read only for a page term loan or revolver whose own class the filing states nothing about.
TERM_LOAN, REVOLVER, NOTES, FACILITY = "term_loan", "revolver", "notes", "facility"
#: The precision a filing states a date at; a comparison is made at that precision, never finer.
DAY, MONTH, YEAR = "day", "month", "year"

_MONTHS = {m: i for i, m in enumerate(
    ("january", "february", "march", "april", "may", "june", "july", "august", "september",
     "october", "november", "december"), start=1)}
_MON = (r"(?:January|February|March|April|May|June|July|August|September|October|November|"
        r"December)")
_DAY_DATE = rf"{_MON}\s+\d{{1,2}}\s*,\s*20\d\d"
_MONTH_DATE = rf"{_MON}\s+20\d\d"
_DATE = rf"(?:{_DAY_DATE}|{_MONTH_DATE})"
_DAY_RE = re.compile(rf"({_MON})\s+(\d{{1,2}})\s*,\s*(20\d\d)", re.I)
_MONTH_RE = re.compile(rf"({_MON})\s+(20\d\d)", re.I)

#: The instrument nouns a loan statement can name. Order matters inside each phrase only through
#: `_phrase_class`: a generic noun ("Credit Agreement") takes the class of a specific one in the
#: same phrase ("Term Loan Credit Agreement", "ABL Credit Facility", "Revolving Credit Facility").
_NOUN = re.compile(
    r"\b(?:(?P<tl>term\s+(?:loan|facilit)\w*|term\s+[a-z](?:-\d)?\s+(?:loans?|facilit\w*)|"
    r"delayed\s+draw\s+term\w*|(?:incremental|initial|refinancing)\s+term\s+loans?)"
    r"|(?P<rc>revolv\w*|ABL\b|asset[- ]based|lines?\s+of\s+credit)"
    r"|(?P<gen>credit\s+(?:agreement|facilit\w*)|facilit(?:y|ies)))", re.I)
#: A facility of another kind — not a term loan or revolver the panel's classes describe. A
#: statement whose phrase names one is read as no class at all.
_OTHER_FACILITY = re.compile(
    r"\b(?:securiti[sz]ation|receivables?|bridge|letters?\s+of\s+credit|commercial\s+paper|"
    r"swap|hedg\w*|lease\w*|DDTL)\b", re.I)
#: A phrase's own boundary: a specific noun this far back without punctuation is the same phrase.
_PHRASE_BACK = 40

#: A simple maturity statement. ``past`` marks the superseded tense ("was scheduled to mature",
#: "would have expired"); ``subj`` is the instrument a "maturity date of <X> is <D>" names.
_STATEMENT = re.compile(
    rf"(?P<verb>(?P<past>(?:was|were)\s+scheduled\s+to\s+(?:mature|expire|terminate)|"
    rf"would\s+have\s+(?:expired|matured|terminated))"
    rf"|(?:is|are)\s+scheduled\s+to\s+(?:mature|expire|terminate)"
    rf"|scheduled\s+to\s+(?:mature|expire|terminate)"
    rf"|(?:will|shall)\s+(?:mature|expire|terminate)"
    rf"|matures|mature|maturing|matured|expires|expiring"
    rf"|due\s+in\s+full\s+on|paid\s+at\s+maturity\s+on|payable\s+at\s+maturity\s+on"
    rf"|(?:with\s+)?an?\s+(?:final\s+)?(?:stated\s+)?maturity\s+date\s+of"
    rf"|(?:final\s+)?(?:scheduled\s+)?(?:stated\s+)?(?:maturity|termination|expiration)\s+date"
    rf"\s+(?:of|for)\s+(?P<subj>[^.;]{{1,220}}?)\s+(?:is|remains|will\s+be|shall\s+be"
    rf"|(?P<was>was)))"
    rf"\s+(?:on\s+|in\s+)?(?P<date>{_DATE})", re.I)
#: A loan named with its year ("ABL Credit Facility due 2031", "Term Loan Credit Agreement due
#: 2030") — year precision, read off the phrase right before "due".
_NAME_DUE = re.compile(r"\bdue\s+(?P<year>20\d\d)\b(?!\s*[,/-]?\s*\d)", re.I)
#: An extension or refinancing: the OLD date superseded, the NEW one current.
_TRANSITION = re.compile(
    rf"\b(?:extend\w*|extension\s+of)\s+(?:the\s+)?(?:existing\s+)?(?:stated\s+|final\s+|"
    rf"scheduled\s+)?(?:maturity|termination|expiration)(?:\s+dates?)?"
    rf"(?:\s+(?:of|for|under)\s+(?P<subj>[^;]{{1,250}}?))?"
    rf"(?:\s+from\s+(?P<old>{_DATE})\s*,?)?"
    rf"(?:\s+by\s+(?:one|two|three|four|five|\d)\s+(?:years?|months?))?"
    rf"\s+to\s+(?P<new>{_DATE}|the\s+earlier\s+of)", re.I)
_REFINANCE = re.compile(
    rf"\brefinanc\w*\s+(?P<old>[^;]{{0,300}}?)\s+with\s+(?:a\s+|an\s+)?new\s+(?P<new>[^;]{{0,200}}?)"
    rf"\b(?:maturing|matures|due)\s+(?:on\s+)?(?P<date>{_DATE})", re.I)
#: "the earlier of (i) <a> and (ii) <b>" — one leg a date (the stated maturity), the other the
#: springing condition.
_EARLIER_OF = re.compile(
    r"\(i\)\s*(?P<a>[^()]{1,200}?)\s*,?\s*and\s+\(ii\)\s*(?P<b>[^().;]{1,200})", re.I)
#: A statement about a facility that has since been replaced: its dates are superseded. Read in the
#: `_PRIOR_BACK` characters before the statement, outside any springing clause. The defined terms
#: are CASE-SENSITIVE — a case-blind "prior" read VRRM's springing "91 days prior to" as a prior
#: facility and retired the ABL's current 2030-10-17.
_PRIOR = re.compile(
    r"\b(?:Existing|Prior|Previous)\b|\b(?:[Pp]reviously|[Pp]redecessor|[Ff]ormer(?:ly)?|"
    r"amends\s+and\s+restates|which\s+provided\s+for|would\s+have)\b")
_PRIOR_BACK = 250
#: Where a springing clause starts. The clause runs to its closing parenthesis or the sentence end.
_SPRING = re.compile(
    r"\b(?:subject\s+to\s+an\s+earlier\s+maturity|springing\s+maturity|will\s+instead\s+mature|"
    r"provided\s+that\s+if)\b", re.I)
_SPRING_DAYS = re.compile(
    rf"(?P<days>\d{{1,3}})\s+days\s+(?:prior\s+to|before)\s+(?:the\s+)?(?P<ref>{_DAY_DATE})", re.I)
_SPRING_WILL_BE = re.compile(
    rf"\bthen\s+the\s+maturity\s+date\s+of\s+[^.;]{{0,160}}?\s+will\s+be\s+(?P<d>{_DAY_DATE})",
    re.I)

#: A coupon, then the notes it names (or the reverse), then the maturity.
_COUPON = r"(?P<c>\d{1,2}(?:\.\d{1,4})?)\s*(?:%|percent\b)"
_NOTE_WORD = r"\b(?:notes?|debentures?|bonds?)\b"
_NOTE_WORD_RE = re.compile(_NOTE_WORD, re.I)
_NOTE_DUE = (rf"\b(?:due|maturing|matur(?:es|ed|e)\s+(?:on|in))\s+(?:in\s+|on\s+)?"
             rf"(?P<date>{_DAY_DATE}|{_MONTH_DATE}|20\d\d\b)")
_NOTES_FWD = re.compile(rf"{_COUPON}(?P<mid>[^%.;:]{{0,90}}?){_NOTE_WORD}(?P<tail>[^%.;]{{0,40}}?)"
                        rf"{_NOTE_DUE}", re.I)
_NOTES_REV = re.compile(rf"{_NOTE_WORD}\s*,?\s*{_COUPON}\s*,?\s*{_NOTE_DUE}", re.I)
_NOTES_DATE_FIRST = re.compile(
    rf"(?P<date>{_DAY_DATE})\s+maturity\s+date\s+of\s+[^.;%]{{0,90}}?{_COUPON}[^.;%]{{0,40}}?"
    rf"{_NOTE_WORD}", re.I)
_SENTENCE = re.compile(r"(?<=[.])\s+(?=[A-Z(“\"•·])")
_QUOTE_CAP = 240
_CLAUSE_CAP = 400


@dataclass(frozen=True)
class Springing:
    """A maturity that moves EARLIER on a condition the filing states."""

    clause: str                 # verbatim, single-spaced, ≤ _CLAUSE_CAP ("…" when cut)
    springs_to: date | None     # only where the filing fixes it (N days before a stated date)


@dataclass(frozen=True)
class Stated:
    """One maturity the filing states for an instrument class."""

    cls: str                    # TERM_LOAN | REVOLVER | NOTES | FACILITY
    key: str                    # "" | "364" (a 364-day revolver) | the notes' coupon ("5.5")
    when: date
    precision: str              # DAY | MONTH | YEAR
    current: bool               # False: superseded (an old date, a prior facility)
    quote: str                  # verbatim, single-spaced, ≤ _QUOTE_CAP ("…" leads a cut)
    springing: tuple[Springing, ...] = ()
    refinance: bool = False     # the new date of a refinancing ("… with a new … maturing on")


def _date(s: str) -> tuple[date, str] | None:
    s = " ".join(s.split())
    if m := _DAY_RE.fullmatch(s):
        try:
            return date(int(m.group(3)), _MONTHS[m.group(1).lower()], int(m.group(2))), DAY
        except ValueError:
            return None
    if m := _MONTH_RE.fullmatch(s):
        return date(int(m.group(2)), _MONTHS[m.group(1).lower()], 1), MONTH
    if re.fullmatch(r"20\d\d", s):
        return date(int(s), 1, 1), YEAR
    return None


def _quote(text: str, lo: int, hi: int) -> str:
    """The verbatim span, single-spaced. A long one keeps its END — the date it states — and
    opens with "…" to say it was cut."""
    flat = " ".join(text[max(0, lo):hi].split())
    return flat if len(flat) <= _QUOTE_CAP else "…" + flat[-(_QUOTE_CAP - 1):].lstrip()


def _phrase_class(text: str, noun: re.Match[str]) -> tuple[str, str] | None:
    """The class of the phrase a noun heads, and its key ("364" for a 364-day revolver).

    A generic noun takes the class of a specific one in the same phrase; a phrase naming a
    facility of another kind (a securitization, a bridge) is no class at all."""
    lo = max(0, noun.start() - _PHRASE_BACK)
    back = text[lo:noun.start()]
    cut = max(back.rfind(p) for p in (".", ",", ";", "(", ")", "“", "”", '"'))
    phrase = (back[cut + 1:] if cut != -1 else back) + noun.group(0)
    if _OTHER_FACILITY.search(phrase):
        return None
    key = "364" if "364" in phrase else ""
    if noun.group("tl"):
        return TERM_LOAN, ""
    if noun.group("rc"):
        return REVOLVER, key
    specific = [m for m in _NOUN.finditer(phrase) if m.group("tl") or m.group("rc")]
    if specific:
        return (TERM_LOAN, "") if specific[-1].group("tl") else (REVOLVER, key)
    return (REVOLVER, "364") if key else (FACILITY, "")


def _classes_in(text: str) -> list[tuple[str, str]]:
    """Every class a span names, in order, without repeats (a "maturity date of X and Y")."""
    out: list[tuple[str, str]] = []
    for m in _NOUN.finditer(text):
        c = _phrase_class(text, m)
        if c is not None and c not in out:
            out.append(c)
    # a specific class makes a generic noun in the same span redundant ("the existing term loans
    # … under the Credit Agreement")
    if any(c[0] != FACILITY for c in out):
        out = [c for c in out if c[0] != FACILITY]
    return out


def _nearest_class(text: str, pos: int, floor: int) -> tuple[str, str] | None:
    """The class of the nearest instrument noun before ``pos``, not before ``floor`` — None when
    a NOTES noun is nearer: the statement is the notes' (`_notes` reads it). BURL's debt table
    runs "…term loan facility, … matures on September 24, 2031 … Convertible senior notes,
    1.25 %, matures on December 15, 2027", and the nearest LOAN noun gave the notes' date to the
    term loan."""
    best: re.Match[str] | None = None
    for m in _NOUN.finditer(text, floor, pos):
        best = m
    if best is None:
        return None
    if _NOTE_WORD_RE.search(text, best.end(), pos):
        return None
    return _phrase_class(text, best)


def _springing(clause: str) -> Springing:
    days = _SPRING_DAYS.search(clause)
    will_be = _SPRING_WILL_BE.search(clause)
    to: date | None = None
    if days and (ref := _date(days.group("ref"))) is not None:
        to = ref[0] - timedelta(days=int(days.group("days")))
    elif will_be and (d := _date(will_be.group("d"))) is not None:
        to = d[0]
    return Springing(_clip(clause), to)


def _clip(clause: str) -> str:
    """A clause single-spaced and capped — and a cut one SAYS it was cut (BRBR's first cut read
    "…will be December 14, 202" with nothing to show a date had lost its last digit)."""
    flat = " ".join(clause.split())
    return flat if len(flat) <= _CLAUSE_CAP else flat[:_CLAUSE_CAP - 1].rstrip() + "…"


#: Where a springing clause opened outside parentheses stops: the condition's own "will be
#: <date>", the next enumerated item ("…, (iii) reduce the interest rate"), or a semicolon.
_SPRING_STOP = re.compile(r",?\s+\((?:i{1,3}|iv|v|vi{0,3}|[a-h])\)\s|;")


def _spring_spans(sentence: str) -> list[tuple[int, int]]:
    """Each springing clause in a sentence: from its marker to its closing parenthesis (when it
    opened inside one), else to the end of its condition (`_SPRING_STOP`) or the sentence."""
    spans: list[tuple[int, int]] = []
    for m in _SPRING.finditer(sentence):
        opened = sentence.rfind("(", 0, m.start()) > sentence.rfind(")", 0, m.start())
        end = sentence.find(")", m.end()) if opened else -1
        if end == -1:
            will_be = _SPRING_WILL_BE.search(sentence, m.end())
            stop = _SPRING_STOP.search(sentence, m.end())
            ends = [x.end() for x in (will_be,) if x is not None]
            ends += [x.start() for x in (stop,) if x is not None]
            end = min(ends) if ends else len(sentence)
        spans.append((m.start(), end))
    return spans


def _inside(pos: int, spans: list[tuple[int, int]]) -> bool:
    return any(lo <= pos < hi for lo, hi in spans)


def _loans(sentence: str) -> list[Stated]:
    """The term-loan, revolver and generic-facility maturities one sentence states."""
    out: list[Stated] = []
    springs = _spring_spans(sentence)
    taken: list[tuple[int, int]] = list(springs)

    def _attach(after: int) -> tuple[Springing, ...]:
        # the springing clauses that follow a current statement in its own sentence
        return tuple(_springing(sentence[lo:hi]) for lo, hi in springs if lo >= after)

    for m in _TRANSITION.finditer(sentence):
        if _inside(m.start(), springs):
            continue
        subj = m.group("subj")
        classes = (_classes_in(subj) if subj else []) or (
            [c] if (c := _nearest_class(sentence, m.start(), max(0, m.start() - 250))) else [])
        if not classes:
            continue
        taken.append((m.start(), m.end()))
        end = m.end()                     # the quote ends at the date it states
        new_d: tuple[date, str] | None = None
        spring: tuple[Springing, ...] = ()
        if m.group("new").lower().startswith("the earlier"):
            if e := _EARLIER_OF.match(sentence, m.end() + 1) or _EARLIER_OF.search(
                    sentence, m.end(), m.end() + 20):
                a, b = _date(e.group("a").strip()), _date(e.group("b").strip())
                if (a is None) != (b is None):   # exactly one leg is the stated date
                    new_d = a or b
                    other = e.group("b") if a is not None else e.group("a")
                    spring = (Springing(_clip(other), None),)
                taken.append((m.end(), e.end()))
                end = e.end()
        else:
            new_d = _date(m.group("new"))
            spring = _attach(m.end())
        quote = _quote(sentence, m.start(), end)
        old_d = _date(m.group("old")) if m.group("old") else None
        for cls, key in classes:
            if old_d is not None:
                out.append(Stated(cls, key, old_d[0], old_d[1], False, quote))
            if new_d is not None:
                out.append(Stated(cls, key, new_d[0], new_d[1], True, quote, spring))
    for m in _REFINANCE.finditer(sentence):
        cls_new = _classes_in(m.group("new"))
        new_d = _date(m.group("date"))
        if not cls_new or new_d is None:
            continue
        taken.append((m.start(), m.end()))
        quote = _quote(sentence, m.start(), m.end())
        cls, key = cls_new[0]
        out.append(Stated(cls, key, new_d[0], new_d[1], True, quote, _attach(m.end()),
                          refinance=True))
        # an old date the refinancing names is superseded; `read` also retires a sole earlier
        # date of the class stated elsewhere in the filing (`_refinanced`)
        for old in _STATEMENT.finditer(m.group("old")):
            if (od := _date(old.group("date"))) is not None:
                out.append(Stated(cls, key, od[0], od[1], False, quote))
    def _prior(at: int) -> bool:
        return any(not _inside(x.start(), springs)
                   for x in _PRIOR.finditer(sentence, max(0, at - _PRIOR_BACK), at))

    for m in _STATEMENT.finditer(sentence):
        if _inside(m.start(), taken):
            continue
        d = _date(m.group("date"))
        if d is None:
            continue
        subj = m.group("subj")
        classes = (_classes_in(subj) if subj else []) or (
            [c] if (c := _nearest_class(sentence, m.start(), max(0, m.start() - 250))) else [])
        if not classes:
            continue
        current = not (m.group("past") or m.group("was") or _prior(m.start()))
        quote = _quote(sentence, max(0, m.start() - 120), m.end())
        spring = _attach(m.end()) if current else ()
        for cls, key in classes:
            out.append(Stated(cls, key, d[0], d[1], current, quote, spring))
    for m in _NAME_DUE.finditer(sentence):
        if _inside(m.start(), taken):
            continue
        noun = None
        for n in _NOUN.finditer(sentence, max(0, m.start() - 60), m.start()):
            noun = n
        # the year must name the phrase it ends: noun, then only descriptors, then "due"
        if noun is None or re.search(r"[.,;()$%]|\d", sentence[noun.end():m.start()]):
            continue
        c = _phrase_class(sentence, noun)
        if c is None:
            continue
        out.append(Stated(c[0], c[1], date(int(m.group("year")), 1, 1), YEAR,
                          not _prior(noun.start()), _quote(sentence, noun.start() - 40, m.end())))
    return out


def _coupon_key(c: str) -> str:
    return f"{float(c):g}"


def _notes(text: str) -> list[Stated]:
    """The notes maturities a text states, keyed by coupon — the one field that tells a filer's
    series apart (NFLX's two 3.625% series are told apart by their years)."""
    out: list[Stated] = []
    for rx in (_NOTES_FWD, _NOTES_REV, _NOTES_DATE_FIRST):
        for m in rx.finditer(text):
            d = _date(m.group("date"))
            if d is None:
                continue
            out.append(Stated(NOTES, _coupon_key(m.group("c")), d[0], d[1], True,
                              _quote(text, m.start(), m.end())))
    return out


def _refinanced(stated: list[Stated]) -> list[Stated]:
    """A refinancing that names no old date ("refinance the existing … term loans … with a new …
    maturing on October 15, 2032") retires the class's ONE other current date when it is earlier —
    VRRM's 10-Q states the 2021 Term Loan's 2028-03-24 in another sentence. With more than one
    other date the refinanced loan is not identifiable, and nothing is retired."""
    refi = [s for s in stated if s.current and s.refinance]
    out = list(stated)
    for r in refi:
        others = {(s.when, s.precision) for s in out
                  if s.current and (s.cls, s.key) == (r.cls, r.key)
                  and not _same(s.when, s.precision, r.when, r.precision)}
        if len(others) == 1 and next(iter(others))[0] < r.when:
            when, prec = next(iter(others))
            out = [Stated(s.cls, s.key, s.when, s.precision, False, s.quote)
                   if (s.cls, s.key, s.when, s.precision, s.current)
                   == (r.cls, r.key, when, prec, True) else s
                   for s in out]
    return out


def read(text: str) -> list[Stated]:
    """Every maturity the filing text states, current and superseded."""
    stated: list[Stated] = []
    for sentence in _SENTENCE.split(" ".join(text.split())):
        if _NOUN.search(sentence):
            stated += _loans(sentence)
    stated += _notes(" ".join(text.split()))
    return _refinanced(stated)


def _same(a: date, pa: str, b: date, pb: str) -> bool:
    """Two dates agree at the coarser of their two precisions."""
    if YEAR in (pa, pb):
        return a.year == b.year
    if MONTH in (pa, pb):
        return (a.year, a.month) == (b.year, b.month)
    return a == b


def current_dates(stated: list[Stated], cls: str, key: str) -> list[Stated]:
    """The class's CURRENT maturities, one per date: a date the filing also states as superseded
    is dropped, and a coarser statement of a finer one ("due 2031" beside "May 14, 2031") folds
    into it."""
    sup = [s for s in stated if (s.cls, s.key) == (cls, key) and not s.current]
    cur = [s for s in stated if (s.cls, s.key) == (cls, key) and s.current
           and not any(x.precision == s.precision == DAY and x.when == s.when for x in sup)
           and not any(x.precision == DAY and s.precision != DAY
                       and _same(x.when, x.precision, s.when, s.precision) for x in sup)]
    rank = {DAY: 0, MONTH: 1, YEAR: 2}
    out: list[Stated] = []
    for s in sorted(cur, key=lambda s: rank[s.precision]):
        twin = next((o for o in out if _same(o.when, o.precision, s.when, s.precision)), None)
        if twin is None:
            out.append(s)
        elif s.springing and not twin.springing:
            out[out.index(twin)] = Stated(twin.cls, twin.key, twin.when, twin.precision, True,
                                          twin.quote, s.springing)
    return out


def iso(when: date, precision: str) -> str:
    """A date at the precision it was stated: YYYY-MM-DD, YYYY-MM or YYYY."""
    return (when.isoformat() if precision == DAY
            else f"{when.year:04d}-{when.month:02d}" if precision == MONTH else f"{when.year:04d}")


# --- the comparison with the panel ------------------------------------------------------------


@dataclass(frozen=True)
class PanelLine:
    """One panel instrument as the check reads it."""

    index: int
    description: str
    type: str
    coupon: str
    principal_musd: float | None
    maturity: date | None


@dataclass(frozen=True)
class Decision:
    """What ONE filing says about one instrument: agree, differ, or not_run (ambiguous)."""

    check: str                              # "agree" | "differ" | "not_run"
    stated: Stated | None = None            # the filing's date paired with the instrument
    note: str = ""


def panel_key(line: PanelLine) -> tuple[str, str] | None:
    """The class a panel instrument is compared under, from CIQ's own type and coupon; None for a
    type no filing statement names (a lease, commercial paper, other borrowings) or a note with
    no single coupon to key it on."""
    t = line.type.strip().lower()
    if t == "term loans":
        return TERM_LOAN, ""
    if t == "revolving credit":
        return REVOLVER, "364" if "364" in line.description else ""
    if t == "bonds and notes":
        m = re.fullmatch(r"\s*(\d{1,2}(?:\.\d{1,4})?)\s*%\s*", line.coupon or "")
        return (NOTES, _coupon_key(m.group(1))) if m else None
    return None


def _repaid(line: PanelLine, period_end: date | None) -> bool:
    """The panel shows it repaid: no principal, and a maturity before the filing's period end.
    The filing need not state such an instrument, so its absence decides nothing."""
    return (not line.principal_musd and line.maturity is not None and period_end is not None
            and line.maturity < period_end)


def _pair(lines: list[PanelLine], dates: list[Stated], label: str,
          period_end: date | None, *, may_differ: bool) -> dict[int, Decision]:
    """One filing's current dates for a class against the page's instruments of that class.

    AGREE only when the two SETS match — every instrument's date stated, every stated date an
    instrument's. DIFFER only when the pairing is forced: as many dates as instruments, and
    exactly one of each left unmatched — and only where ``may_differ``. Anything else is ambiguous
    and not run. A repaid instrument (`_repaid`) is matched if the filing states its date, and
    otherwise left for an older filing."""
    out: dict[int, Decision] = {}
    if not dates:
        return out
    active = [ln for ln in lines if not _repaid(ln, period_end)]

    def _hit(ln: PanelLine) -> Stated | None:
        return next((s for s in dates if ln.maturity is not None
                     and _same(ln.maturity, DAY, s.when, s.precision)), None)

    for ln in lines:
        if ln not in active and (s := _hit(ln)) is not None:
            out[ln.index] = Decision("agree", s)
    if not active:
        return out
    hits = {ln.index: _hit(ln) for ln in active}
    used = [s for s in dates if any(h is s for h in hits.values())]
    if all(hits.values()) and len(used) == len(dates):
        for ln in active:
            out[ln.index] = Decision("agree", hits[ln.index])
        return out
    if len(active) == len(dates):
        open_lines = [ln for ln in active if hits[ln.index] is None]
        open_dates = [s for s in dates if s not in used]
        if may_differ and len(open_lines) == 1 and len(open_dates) == 1:
            for ln in active:
                out[ln.index] = (Decision("differ", open_dates[0]) if ln is open_lines[0]
                                 else Decision("agree", hits[ln.index]))
            return out
    why = (f"the filing states {len(dates)} current {label} maturit"
           f"{'y' if len(dates) == 1 else 'ies'} and the page lists {len(active)}"
           + ("" if len(active) != len(dates) else ", and they do not pair one-to-one"
              if may_differ else f", and a {label} statement can confirm a date, never move one"))
    for ln in active:
        out[ln.index] = Decision("not_run", None, why)
    return out


_LABEL = {TERM_LOAN: "term-loan", REVOLVER: "revolver", NOTES: "notes", FACILITY: "facility"}


def decide(lines: list[PanelLine], stated: list[Stated],
           period_end: date | None) -> dict[int, Decision]:
    """What one filing decides about the panel's instruments, by class. A term loan or revolver
    the filing states nothing about under its own class is read against the filing's GENERIC
    facility dates ("The 2025 Credit Agreement matures on October 3, 2030"), all such instruments
    pooled — so one generic date can pair only with one such instrument."""
    groups: dict[tuple[str, str], list[PanelLine]] = {}
    for ln in lines:
        # an undated line has nothing to pair, and counting it would break every set it sits in
        if ln.maturity is not None and (k := panel_key(ln)) is not None:
            groups.setdefault(k, []).append(ln)
    out: dict[int, Decision] = {}
    pooled: list[PanelLine] = []
    for (cls, key), members in groups.items():
        dates = current_dates(stated, cls, key)
        if not dates and cls in (TERM_LOAN, REVOLVER) and not key:
            pooled += members
            continue
        label = (f"{key}% notes" if cls == NOTES else
                 f"364-day {_LABEL[cls]}" if key == "364" else _LABEL[cls])
        # A NOTE NEVER DIFFERS. A coupon names a series only up to its coupon, and a filing often
        # mentions one of two same-coupon series: on the corpus BOTH notes differences were that —
        # UBER's 7.5% 2027 notes against an 8-K's 7.5% 2025 series, GOOGL's 4.5% 2035 notes
        # against a 10-Q's 4.5% 2045. A series' maturity is fixed at issue and is not refinanced
        # in place, so a notes difference would catch nothing real and fire on these.
        out.update(_pair(members, dates, label, period_end, may_differ=cls != NOTES))
    if pooled:
        # A GENERIC NOUN NEVER DIFFERS either: "Credit Agreement" does not say which instrument
        # it is. WLK's 10-Q dates its new credit agreement (a revolver) 2031-04-02, and a pooled
        # pairing forced that date onto its $1.0M term loan.
        out.update(_pair(pooled, current_dates(stated, FACILITY, ""), "credit-facility",
                         period_end, may_differ=False))
    return out


# --- the check: every panel maturity against the newest filing that states it -----------------


@dataclass(frozen=True)
class Source:
    """One filing the check reads: what it is, and what it states (None: it could not be read)."""

    form: str
    accession: str
    filed: date
    read_as: str
    period_end: date | None = None     # a 10-Q/10-K's balance-sheet date (`_repaid`)
    stated: tuple[Stated, ...] | None = None
    error: str | None = None

    @property
    def cite(self) -> str:
        return f"{self.form} {self.accession} (filed {self.filed.isoformat()})"


#: How the check reads each kind of source — named on the page beside the accession.
READ_PERIODIC = "the latest periodic report"
READ_AFTER_PANEL = "an 8-K after the panel"
READ_LINKED = "an 8-K the page links"


def check(lines: list[PanelLine], sources: list[Source], *, panel_filed: date | None,
          bound: date, unread: str | None = None) -> MaturityCheck:
    """Each panel instrument against the NEWEST source that decides it.

    A source decides an instrument when its statements pair with it (`decide`): agree, differ, or
    an ambiguity that is reported as not run. An older source never overrides a newer one's
    decision; an instrument no source decides is not run. A difference GOVERNS — the page prints
    the filing's date — when the deciding filing was filed on or after the panel's own source
    filing (the panel could not have known it, or mis-read the very filing it cites) and states
    the day. A panel newer than the filing may reflect a change the filing predates, so the page
    keeps CIQ's date and says so.

    FAIL LOUD. With ``unread`` (the submissions index could not be read) every row is not run with
    that reason. A filing that could not be read is listed with its error, and no OLDER filing
    decides past it: an instrument it might have stated is not run, naming it."""
    ordered = sorted(sources, key=lambda s: (s.filed, s.read_as == READ_PERIODIC), reverse=True)
    decisions = [(s, decide(lines, list(s.stated), s.period_end)) for s in ordered
                 if s.stated is not None]
    failed = next((s for s in ordered if s.stated is None), None)
    rows: list[MaturityCheckRow] = []
    for ln in lines:
        row = _row(ln, decisions, panel_filed)
        readable = panel_key(ln) is not None and ln.maturity is not None
        if readable and (unread is not None or (
                failed is not None and (row.source_filed is None
                                        or date.fromisoformat(row.source_filed) < failed.filed))):
            row = MaturityCheckRow(
                instrument=row.instrument, description=row.description,
                ciq_maturity_date=row.ciq_maturity_date, check=CHECK_NOT_RUN,
                note=unread or (f"the {failed.cite} could not be read ({failed.error}), and no "
                                "newer filing states this maturity" if failed else ""))
        rows.append(row)
    return MaturityCheck(
        panel_filed=panel_filed.isoformat() if panel_filed else None, bound=bound.isoformat(),
        sources=[MaturitySource(form=s.form, accession=s.accession, filed=s.filed.isoformat(),
                                read_as=s.read_as,
                                statements=len(s.stated) if s.stated is not None else 0,
                                error=s.error) for s in ordered],
        rows=rows)


def _row(ln: PanelLine, decisions: list[tuple[Source, dict[int, Decision]]],
         panel_filed: date | None) -> MaturityCheckRow:
    base = {"instrument": ln.index, "description": ln.description,
            "ciq_maturity_date": ln.maturity.isoformat() if ln.maturity else None}
    if panel_key(ln) is None:
        why = ("no single coupon to key the notes on" if ln.type.strip().lower()
               == "bonds and notes" else f"a {ln.type or 'typeless'} line — not a term loan, "
               "revolver or note a filing statement names")
        return MaturityCheckRow(**base, check=CHECK_NOT_RUN, note=why, excluded=True)
    if ln.maturity is None:
        return MaturityCheckRow(**base, check=CHECK_NOT_RUN, note="the panel states no maturity",
                                excluded=True)
    hit = next(((s, d[ln.index]) for s, d in decisions if ln.index in d), None)
    if hit is None:
        return MaturityCheckRow(**base, check=CHECK_NOT_RUN,
                                note="no filing read states a maturity for it")
    src, dec = hit
    if dec.check == CHECK_NOT_RUN or dec.stated is None:
        return MaturityCheckRow(**base, check=CHECK_NOT_RUN, source=src.cite,
                                source_filed=src.filed.isoformat(), note=dec.note)
    st = dec.stated
    also: list[str] = []
    springing: list[SpringingMaturity] = [
        SpringingMaturity(clause=x.clause,
                          springs_to=x.springs_to.isoformat() if x.springs_to else None,
                          source=src.cite) for x in st.springing]
    for other, d in decisions:
        o = d.get(ln.index)
        if other is src or o is None or o.stated is None or o.check == CHECK_NOT_RUN:
            continue
        if _same(o.stated.when, o.stated.precision, st.when, st.precision):
            also.append(other.cite)
            springing += [SpringingMaturity(
                clause=x.clause, springs_to=x.springs_to.isoformat() if x.springs_to else None,
                source=other.cite) for x in o.stated.springing
                if x.clause not in {s.clause for s in springing}]
    differ = dec.check == CHECK_DIFFER
    newer = panel_filed is None or src.filed >= panel_filed
    when, precision, day_note = st.when, st.precision, ""
    if differ and precision != DAY and (day := _day_for(st, [s for s, _ in decisions])):
        when, precision = day[0], DAY
        day_note = f"it states the {st.precision}; the day is from the {day[1]}"
    governs = differ and newer and precision == DAY
    note = (day_note if not differ or governs else
            f"the filing states only the {st.precision}, so the page keeps CIQ's date"
            if newer else
            f"the panel's source filing ({panel_filed.isoformat() if panel_filed else '—'}) is "
            "newer than this one and may reflect a later change, so the page keeps CIQ's date")
    return MaturityCheckRow(
        **base, check=dec.check, filing_maturity=iso(when, precision), source=src.cite,
        source_filed=src.filed.isoformat(), governs=governs, also_stated_by=also,
        quote=st.quote, springing=springing, note=note)


def _day_for(st: Stated, sources: list[Source]) -> tuple[date, str] | None:
    """The DAY of a month- or year-precise difference, where exactly one current day-precise
    statement of the same class — or a generic facility — falls inside it across the filings
    read. TGT's 10-Q dates its new revolver "August 2031"; its 8-K says the Credit Agreement "will
    expire on August 14, 2031". Two candidate days, or none, leave the coarse date."""
    found: dict[date, str] = {}
    for src in sources:
        for x in src.stated or ():
            if (x.current and x.precision == DAY and _same(x.when, DAY, st.when, st.precision)
                    and ((x.cls, x.key) == (st.cls, st.key) or (x.cls, x.key) == (FACILITY, ""))):
                found.setdefault(x.when, src.cite)
    return next(iter(found.items())) if len(found) == 1 else None
