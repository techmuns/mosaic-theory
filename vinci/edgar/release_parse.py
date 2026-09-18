"""(RC-1 A) DETERMINISTIC 8-K EX-99.1 earnings/guidance parser — heading/anchor-targeted, never an
LLM. Extracts, each source-bound to the exhibit: guidance ranges (+ QUALITATIVE-only markers where
the outlook names a metric but states no number), non-GAAP reconciliation ACTUALS, one-off items
(impairments/charges), and event-impact quantifications (the Avis class, 'expects to reduce X by
$A-$B').

Fail-loud (the PR-2 lesson): no anchored pattern → the field is simply absent + a ``qa_flag``
'no anchored pattern matched — {kind}', never a guessed number and never an analyst caveat. Coverage
is partial beyond the pinned names (guidance phrasing varies across the universe); a miss is honest
UNKNOWN, and an LLM-fenced escalation tier is a QUEUED item, built only on future-finalist evidence.

Text is read pre-normalized (vinci.graph.filings.normalize_text folds the nbsp EDGAR renders as
'$44.7\xa0million'), so a literal space in these anchors matches.
"""
from __future__ import annotations

import html
import re
from typing import NamedTuple

from vinci.dossier.schemas import (
    DriverKind,
    EventImpact,
    GuidanceItem,
    OneOffItem,
    OperatingDriver,
    ReconciliationValue,
    ReleaseExtract,
)
from vinci.netcache import CachedHttp, HttpError
from vinci.resolver.index import pad_cik

_INDEX = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/index.json"
_ARCHIVE = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{doc}"
_HEADERS = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{acc_dashed}-index-headers.html"

# TOLERANT Ex-99.1 filename match — the FALLBACK only (see exhibit_991_urls): 'ex991' / 'dex991' /
# 'ex-99.1' / 'ex99_1', any separators including the '_' WORD char that a \W* class drops.
# The final '1' + (?!\d) exclude 99.2 / 99.10. Filenames are a GUESS: filers also ship
# 'a991_pressrelease…', 'exhibit991…', 'exh991…' (unmatched here), and EPAM's 'exhibit99_q1x2026'
# matches only by the accident of "q1" — which is precisely why the TYPE lookup below leads.
_EX991_NAME = re.compile(r"ex[\W_]*99[\W_]*d?[\W_]*1(?!\d)", re.I)
# EDGAR's own per-document SGML header: <TYPE>EX-99.1 … <FILENAME>whatever.htm. Served
# HTML-ESCAPED inside the -index-headers page, so the caller unescapes before matching.
_SGML_DOC = re.compile(r"<TYPE>([^\s<]+)[\s\S]{0,400}?<FILENAME>([^\s<]+)", re.I)
_TEXT_DOC = (".htm", ".html", ".txt")


def _is_ex991(name: str) -> bool:
    """Filename-shaped guess at an Ex-99.1 press release (the fallback path)."""
    low = name.lower()
    return low.endswith(_TEXT_DOC) and _EX991_NAME.search(low) is not None


def _ex991_names_from_headers(http: CachedHttp, cik: str, accession: str) -> list[str] | None:
    """Filenames EDGAR itself types as EX-99.1, from the filing's SGML header.

    The AUTHORITATIVE source: the header states the exhibit designator, so no filename convention
    has to be guessed. Returns None when the header is unreachable/unparseable (caller falls back
    to the filename match) — distinct from [] which means 'read it, this filing furnishes none'."""
    acc = accession.replace("-", "")
    url = _HEADERS.format(cik=int(pad_cik(cik)), acc=acc, acc_dashed=accession)
    try:
        raw = http.get_text(url, ttl_seconds=None)
    except (HttpError, ValueError):
        return None
    text = html.unescape(raw)
    if "<TYPE>" not in text.upper():
        return None  # not the SGML shape we expect — fall back rather than assert absence
    return [
        fn for ty, fn in _SGML_DOC.findall(text)
        # EX-99.1 exactly — never EX-99.11/99.12, and never the EX-99.2 sibling
        # EX-99.1 or a bare EX-99 — never EX-99.11/99.12, and never the EX-99.2 sibling. The bare
        # form was missing until 2026-09-18: PARR types its quarterly release `EX-99`, so its
        # Q3-2025 earnings release was invisible and the page carried "carries 2.02 but no EX-99.1
        # exhibit was found" against a filing that plainly furnishes one. Measured over the fleet
        # (22 names, their 10 most recent 8-Ks): 29 filings carry 2.02/8.01 with no release found,
        # and exactly 2 of those furnish one under this type — PARR's and LLY's. The other 27 are
        # genuinely release-free (debt take-downs with EX-1.1/EX-4.x, XBRL-only 8-Ks).
        if re.fullmatch(r"ex-?99(?:[.\-]?1)?", ty.strip(), re.I) and fn.lower().endswith(_TEXT_DOC)
    ]


def exhibit_991_urls(http: CachedHttp, cik: str, accession: str) -> list[str]:
    """ALL furnished Exhibit-99.1 press-release URLs in a filing (not first-match — a filing can
    carry more than one, and both must parse).

    ``EX-99.1`` and the bare ``EX-99`` both count — filers use either for the furnished release.

    Reads the exhibit TYPE from EDGAR's SGML header rather than pattern-matching the FILENAME:
    filers name the same exhibit 'ex991', 'a991_pressrelease…', 'exhibit991…', 'exh991…' and
    'exhibit99_q1x2026', so a filename rule is a guess that silently loses press releases (measured
    2026-07-22: 24 of 53 across five names). The filename match stays as the fallback for a filing
    whose header cannot be read. Empty when the filing genuinely furnishes no Ex-99.1."""
    acc = accession.replace("-", "")
    names = _ex991_names_from_headers(http, cik, accession)
    if names is None:  # header unreadable → fall back to the filename guess
        try:
            idx = http.get_json(_INDEX.format(cik=int(pad_cik(cik)), acc=acc), ttl_seconds=None)
        except (HttpError, ValueError):
            return []
        names = [
            str(item.get("name", ""))
            for item in idx.get("directory", {}).get("item", [])
            if _is_ex991(str(item.get("name", "")))
        ]
    return [_ARCHIVE.format(cik=int(pad_cik(cik)), acc=acc, doc=n) for n in names]


# --- helpers -------------------------------------------------------------------------------------

_PERIOD = re.compile(r"\b(Q[1-4]\s+20\d\d|FY\s*20\d\d|(?:fiscal\s+)?20\d\d)\b", re.I)


def _near(a: float, b: float, *, tol: float = 0.10) -> bool:
    """Two magnitudes close enough to be the SAME item restated at a different rounding
    ($11.0M vs $11.3M), rather than two different charges ($12.0M vs $30.0M)."""
    hi = max(abs(a), abs(b))
    return hi == 0 or abs(a - b) / hi <= tol


def _money(s: str) -> float | None:
    try:
        return float(s.replace(",", "").replace("$", "").strip())
    except ValueError:
        return None


def _verbatim(text: str, start: int, end: int, *, cap: int = 200) -> str:
    """A ≤cap-char verbatim window, snapped back to the enclosing bullet/sentence, single-spaced."""
    lo0 = max(0, start - 170)
    b = max(text.rfind("•", lo0, start), text.rfind(". ", lo0, start))
    lo = (b + 1) if b != -1 else start
    return " ".join(text[lo:end].split())[:cap].strip()


def _period_near(text: str, start: int, end: int) -> str:
    m = _PERIOD.search(text, end, min(len(text), end + 60)) or _PERIOD.search(
        text, max(0, start - 60), start
    )
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""


# The DIRECTION a release states beside the level: "…$230.0 million, an increase of $21.5 million",
# "…of $3.26, an increase of 14.2%", "Revenues of $1.408 billion, up 12.8% year-over-year".
# A gap-down is about the DELTA, not the level, so the level alone cannot explain it.
_CHANGE = re.compile(
    r"^[^.•]{0,60}?\b(?:(an\s+increase|a\s+decrease|an\s+improvement|a\s+decline)\s+of|"
    r"(up|down|rose|fell|declined|increased|decreased))\s+"
    r"(?:by\s+)?(\$?\s*[\d,.]+\s*(?:million|billion|%)?)",
    re.I,
)
_DOWNWORDS = ("decrease", "decline", "down", "fell", "declined", "decreased")


def _change_after(text: str, end: int) -> str | None:
    """The change clause immediately following a metric's value, normalised to a signed token.

    Read only from the SAME sentence/bullet as the value (the window stops at the next '.'/'•'),
    so a delta belonging to a later metric is never attached to this one."""
    stop = len(text)
    for mark in (". ", "•", "; "):
        j = text.find(mark, end, end + 160)
        if j != -1:
            stop = min(stop, j)
    m = _CHANGE.search(text[end:stop])
    if not m:
        return None
    word = (m.group(1) or m.group(2) or "").lower()
    amt = " ".join(m.group(3).split()).replace("$ ", "$")
    sign = "-" if any(w in word for w in _DOWNWORDS) else "+"
    return f"{sign}{amt}"


def _norm_metric(raw: str) -> str:
    r = raw.lower()
    if "ebitda" in r:
        return "adjusted ebitda"
    if "per share" in r or "eps" in r:
        return "adjusted eps"
    # operating income / income from operations is PRE interest and tax — bucketing it into
    # "adjusted net income" (the old fall-through) states a different figure under a familiar
    # name, which is worse than not extracting it. It gets its own label.
    if "operating income" in r or "income from operations" in r:
        return "adjusted operating income"
    return "adjusted net income"


class _ReleaseFrame(NamedTuple):
    """What a release's HEADER says it covers. A figure falls back to this only when its own
    sentence, its comparison clause and its section heading are all silent about its period.

    ``kind`` is ``"quarter"`` (one quarter), ``"annual"`` (one fiscal year), ``"combined"`` (a
    fourth quarter AND its full year in one exhibit) or ``"unknown"``. Only the first two name a
    single period, so only they may LABEL an unattributed figure. A combined release carries a Q4
    figure and an FY figure side by side under one header, and the header cannot say which a given
    number is — that is the defect this frame exists to stop repeating."""

    kind: str
    quarter: int | None
    year: str | None
    # fiscal year minus the calendar year of the release's own quarter-end date. A fiscal-year filer
    # (BellRing: Q1 FY2026 is the three months ended December 31, 2025) names its quarters by the
    # year they END in, so "three months ended December 31, 2025" is Q1 2026, not Q1 2025.
    fy_offset: int = 0

    @property
    def label(self) -> str:
        if self.kind in ("quarter", "combined") and self.quarter and self.year:
            return f"Q{self.quarter} {self.year}"
        return self.year or ""


_QN = {"first": 1, "1st": 1, "second": 2, "2nd": 2, "third": 3, "3rd": 3, "fourth": 4, "4th": 4}

#: "Fourth Quarter and Full Year 2025" / "…and Fiscal Year 2025" / "Fiscal Fourth Quarter and Full
#: Fiscal Year 2025" / "FOURTH QUARTER AND 2025" / "Fourth Quarter and Annual 2025". Fourth quarter
#: only: no other quarter is ever reported beside its full year.
_HDR_COMBINED = re.compile(
    r"(?:fiscal\s+)?(?:fourth|4th)\s+quarter\s+(?:(?:of\s+)?(?:fiscal\s+)?(?:year\s+)?20\d\d\s+)?"
    r"and\s+(?:the\s+)?(?:(?:full|fiscal|annual|entire)\s+){0,2}(?:fiscal\s+)?(?:year\s+)?(20\d\d)",
    re.I)
# "Second Quarter of Fiscal Year 2026" / "of 2026" / "of fiscal 2026" — the FY phrasing between
# 'quarter' and the year must not push this to the bare-year fallback (BellRing mislabelled its
# quarterly figures with the year).
_HDR_QUARTER = re.compile(
    r"(first|second|third|fourth)\s+quarter\s+"
    r"(?:of\s+)?(?:the\s+)?(?:fiscal\s+year\s+|fiscal\s+|fy\s*)?(20\d\d)",
    re.I)
#: "Reports 2025 Financial Results" / "Reports Full Year 2025 Financial Results" — one year, no
#: quarter named anywhere in the header.
_HDR_ANNUAL = re.compile(
    r"(?:reports?|announces?)\s+"
    r"(?:(?:full|fiscal|annual)[- ](?:fiscal\s+)?(?:year\s+)?)?(20\d\d)\s+"
    r"(?:(?:full[- ]year|fiscal[- ]year|annual|financial)\s+)*results"
    r"|(?:full|fiscal)[- ]year\s+(20\d\d)\s+(?:financial\s+)?results",
    re.I)
_HDR_ANY_YEAR = re.compile(r"(?:reports|results|full[- ]year|fiscal)\D{0,25}?(20\d\d)", re.I)


def _release_frame(text: str) -> _ReleaseFrame:
    """Classify the header. COMBINED is tested FIRST: its text also contains a quarter phrase, and
    WERN's "Fourth Quarter and Annual 2025 Results" was read as a plain Q4 release only because a
    "Fourth Quarter 2025 Highlights" subheading happened to fall inside the header window."""
    head = text[:600]
    if c := _HDR_COMBINED.search(head):
        return _ReleaseFrame("combined", 4, c.group(1), _fy_offset(text, c.group(1)))
    if q := _HDR_QUARTER.search(head):
        return _ReleaseFrame("quarter", _QN[q.group(1).lower()], q.group(2),
                             _fy_offset(text, q.group(2)))
    if a := _HDR_ANNUAL.search(head):
        return _ReleaseFrame("annual", None, a.group(1) or a.group(2))
    y = _HDR_ANY_YEAR.search(head) or re.search(r"(20\d\d)", head)
    return _ReleaseFrame("unknown", None, y.group(1) if y else None)


def _fy_offset(text: str, year: str) -> int:
    """The header's fiscal year minus the LATEST calendar year a "three months / quarter ended
    <date>" phrase names — the release's own quarter end. 0 when the text names no such date, or
    when the gap is not a plausible fiscal-year shift (−1..1)."""
    ends = [int(m.group("qey")) for m in _PHRASE.finditer(text) if m.group("qended")]
    if not ends:
        return 0
    off = int(year) - max(ends)
    return off if -1 <= off <= 1 else 0


def _release_period(text: str) -> str:
    """The release's PRIMARY period as a display label — the quarter for a quarterly or combined
    release, the year for an annual one. Figures are NOT labelled from this; see _figure_period."""
    return _release_frame(text).label


_MONTH = (r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?|"
          r"sept?(?:ember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\.?")
#: Every way a release names the period a figure belongs to, most specific first. ORDER MATTERS:
#: at one position the first alternative wins, so "the prior year fourth quarter" must be read as
#: a relative QUARTER before "the prior year" can claim it, and a date must swallow its own year
#: before the bare-year alternative sees it (WERN's "$0.53 in the prior year OMAHA, Neb., February
#: 5, 2026" was labelled 2026 — the dateline, not the period).
_PHRASE = re.compile(
    r"(?P<ytd>\bytd\b|year[- ]to[- ]date|\b(?:six|nine)[- ]months?\s+ended|"
    r"first\s+(?:half|six\s+months|nine\s+months)|first\s+three\s+quarters)"
    rf"|(?P<qended>(?:three[- ]months?|quarter)\s+ended\s+"
    rf"{_MONTH}\s+\d{{1,2}},?\s+(?P<qey>20\d\d))"
    rf"|(?P<yended>(?:twelve[- ]months?|(?:fiscal\s+)?year)\s+ended\s+"
    rf"{_MONTH}\s+\d{{1,2}},?\s+(?P<yey>20\d\d))"
    r"|(?P<relq>(?:the\s+)?"
    r"(?:prior[- ](?:fiscal[- ])?year|previous[- ]year|year[- ]ago|comparable|same)"
    r"\s+(?:(?P<relqn>first|second|third|fourth)\s+)?(?:fiscal\s+)?quarter)"
    r"|(?P<q>(?:fiscal\s+)?(?P<qn>first|second|third|fourth|1st|2nd|3rd|4th)\s+(?:fiscal\s+)?quarter"
    r"(?:\s+of)?(?:\s+(?:the\s+)?(?:fiscal\s+)?(?:year\s+)?(?P<qy>20\d\d))?)"
    r"|(?P<qs>\bq(?P<qsn>[1-4])\s*(?:fiscal\s*|fy\s*)?'?(?P<qsy>20\d\d))"
    r"|(?P<quarterly>\bquarterly\b)"
    r"|(?P<fy>(?:full|fiscal|entire)[- ](?:fiscal[- ])?year(?:\s+(?:of\s+)?(?P<fyy>20\d\d))?|"
    r"\b(?:fiscal|fy)\s*'?(?P<fyy2>20\d\d))"
    r"|(?P<relp>(?:the\s+)?(?:prior|previous)[- ](?:fiscal\s+)?year(?:\s+period)?|"
    r"(?:the\s+)?(?:comparable\s+)?year[- ]ago\s+period|"
    r"(?:the\s+)?same\s+period(?:\s+(?:in|of)\s+(?P<relpy>20\d\d))?)"
    rf"|(?P<date>{_MONTH}\s+\d{{1,2}},?\s+20\d\d)"
    r"|(?P<bare>\b(?P<bareyear>20\d\d)\b)",
    re.I)
#: A comparison clause: the prior-period value is introduced by one of these.
_CMP = re.compile(
    r"\b(?:compared\s+(?:to|with)|as\s+compared\s+to|versus|vs\.)"
    # "Gross margin increased from 32.5% to 34.7%": the FROM value is the comparison. Only a
    # number may follow, so "income from operations" is not one.
    r"|\bfrom\s+(?=\(?\$?\s*\d)",
    re.I)
#: A period phrase TRAILING a figure only counts when a preposition introduces it: "$8.6 million …
#: in the fourth quarter of 2025", "$113.1 million for the fourth quarter". Without this, the next
#: section's heading bleeds in — WERN's Q4 "$0.05, down 29% 2025 Highlights" read as the full year.
_INTRO = re.compile(r"\b(?:in|for|during|of|over|through|throughout)\s+(?:the\s+)?$", re.I)
#: Forward-looking words. A figure under one of these is an OUTLOOK, not a reported actual —
#: "We currently expect: ● Fiscal 2026 Pro Forma Adjusted EBITDA of $80" (FUBO).
_FORWARD = re.compile(
    r"\b(?:expects?|expected|expecting|anticipates?|anticipated|outlook|guidance|guides?|"
    # "projects" is a NOUN in a release far more often than a verb — Bolt Projects Holdings' own
    # name dropped its "revenue of $0.4 million in Q3 2025" — so only its verb forms count. "target"
    # stays in EVERY form: as a noun it is still a goal ("well on track toward our target gross
    # margin of 60%", Bolt, the same release), and dropping it filed that target as Q4's actual.
    # "forecast" in every form: "The Company is forecasting Adjusted EBITDA of $1.19 to $1.24
    # billion" (Antero Midstream) was filed as Q4's actual and displaced the real $285 million.
    r"forecast\w*|projected|projecting|targets?|targeted|targeting|"
    r"(?:we|company|management)\s+(?:projects|project)|"
    r"reaffirm\w*|revis(?:e|es|ed|ing)\s+its)\b",
    re.I)
_AMOUNT = re.compile(r"\$\s*\(?\d|\d[\d,.]*\s*(?:million|billion)\b", re.I)
#: One stated amount in a clause lead, with its scale word when there is one ("$27.6 million",
#: "$0.05") — how a comparison finds the current value it is the prior of.
_LEAD_AMOUNT = re.compile(r"\$\s*\(?([\d,]*\.?\d+)\)?\s*(million|billion)?", re.I)
#: A CHANGE amount's lead-in — the delta beside a figure is not the figure its comparison is about.
_CHANGE_LEAD = re.compile(
    r"\b(?:(?:an?\s+)?(?:increase|decrease|improvement|decline|growth|reduction|change)\s+of|"
    r"(?:up|down|increased|decreased|grew|declined|rose|fell|improved)(?:\s+by)?)\s*$", re.I)
#: Clause edges — a sentence end or any bullet glyph a release uses. "·" (middle dot) included:
#: Ribbon's "· Non-GAAP Adjusted EBITDA was $40 million, compared to $55 million for the fourth
#: quarter of 2024" ran into the bullet before it, whose comparison made the Q4 2025 figure a prior.
_EDGE = re.compile(r"\.\s|[•●○◦■▪·]")
#: A section heading that names ONE period ("Fourth Quarter Fiscal 2025 Highlights", "Fiscal Year
#: 2025 Summary"). Title Case is required so prose ("fourth quarter results reflect…") is not a
#: heading; a heading naming BOTH periods ("Fourth Quarter and Fiscal Year 2025 Highlights") says
#: nothing about any one figure under it.
_HEADING = re.compile(
    # Words may carry digits: FuboTV heads a section "Q3 Fiscal 2026 Highlights", and a letters-only
    # word broke the run at "Q3" and read the heading as "Fiscal 2026" — a full-year section.
    r"((?:[A-Z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)*|20\d\d)"
    r"(?:\s+(?:[A-Z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)*|20\d\d|and)){0,6})"
    r"\s+(?:Financial\s+)?(Highlights|Summary|Overview|Results)\b")
#: "Results" alone is too common a word to trust as a heading ("2024 Results" inside a VITL
#: exhibit labelled its Q2-2025 gross margin as the full year 2024); it needs a period WORD.
_PERIOD_WORD = re.compile(
    r"\b(?:quarter|year|fiscal|annual|months|ytd|year-to-date|q[1-4])\b", re.I)


_NO = object()  # "this phrase is not evidence either way — keep looking"


def _phrases(text: str, lo: int, hi: int) -> list[re.Match[str]]:
    return list(_PHRASE.finditer(text, max(0, lo), max(lo, hi)))


def _year_minus(year: str | None, n: int = 1) -> str | None:
    return str(int(year) - n) if year else None


def _as_current(m: re.Match[str], frame: _ReleaseFrame) -> object:
    """What a period phrase in a CURRENT figure's own clause says that figure is. Returns a label,
    ``None`` (a period this extractor must not label — a year-to-date figure), or ``_NO``."""
    g = m.groupdict()
    if g["ytd"]:
        return None
    if g["q"]:
        year = g["qy"] or frame.year
        return f"Q{_QN[g['qn'].lower()]} {year}" if year else None
    if g["qs"]:
        return f"Q{g['qsn']} {g['qsy']}"
    if g["qended"]:
        return (f"Q{frame.quarter} {int(g['qey']) + frame.fy_offset}"
                if frame.quarter and frame.kind in ("quarter", "combined") else None)
    if g["quarterly"]:
        return frame.label if frame.kind in ("quarter", "combined") else None
    if g["fy"]:
        year = g["fyy"] or g["fyy2"]
        if not year and frame.kind in ("combined", "annual"):
            year = frame.year
        return year if year else None
    if g["yended"]:
        return g["yey"]
    if g["bare"]:
        # In a single-quarter release a bare year beside a figure is far likelier an outlook or a
        # date than a claim that the figure is annual — the header's quarter stands.
        return _NO if frame.kind == "quarter" else g["bareyear"]
    return _NO  # relative phrases and dates describe a comparison, never the current figure


def _as_comparison_granularity(m: re.Match[str], frame: _ReleaseFrame) -> object:
    """What a comparison clause's period says about the CURRENT figure's period: "compared with
    $346.7 million in the prior year fourth quarter" makes the current value a Q4; "compared to
    $44.8 million in 2024" makes it the full year after."""
    g = m.groupdict()
    if g["ytd"]:
        return None
    if g["q"]:
        n = _QN[g["qn"].lower()]
        year = str(int(g["qy"]) + 1) if g["qy"] else frame.year
        return f"Q{n} {year}" if year else None
    if g["qs"]:
        return f"Q{g['qsn']} {int(g['qsy']) + 1}"
    if g["relq"]:
        rn = _QN[g["relqn"].lower()] if g["relqn"] else frame.quarter
        return f"Q{rn} {frame.year}" if rn and frame.year else None
    if g["qended"]:
        return (f"Q{frame.quarter} {int(g['qey']) + 1 + frame.fy_offset}"
                if frame.quarter else None)
    if g["fy"]:
        year = g["fyy"] or g["fyy2"]
        return str(int(year) + 1) if year else _NO
    if g["yended"]:
        return str(int(g["yey"]) + 1)
    if g["bare"]:
        return _NO if frame.kind == "quarter" else str(int(g["bareyear"]) + 1)
    return _NO  # "the prior year" / "the comparable year ago period" carry no granularity


def _as_prior(m: re.Match[str], frame: _ReleaseFrame) -> object:
    """The period of a COMPARISON figure itself, from its own trailing clause."""
    g = m.groupdict()
    if g["ytd"]:
        return None
    if g["q"]:
        return f"Q{_QN[g['qn'].lower()]} {g['qy']}" if g["qy"] else None
    if g["qs"]:
        return f"Q{g['qsn']} {g['qsy']}"
    if g["relq"]:
        rn = _QN[g["relqn"].lower()] if g["relqn"] else frame.quarter
        return f"Q{rn} {_year_minus(frame.year)}" if rn and frame.year else None
    if g["qended"]:
        return f"Q{frame.quarter} {int(g['qey']) + frame.fy_offset}" if frame.quarter else None
    if g["fy"]:
        return g["fyy"] or g["fyy2"] or None
    if g["yended"]:
        return g["yey"]
    if g["relp"]:
        if frame.kind == "quarter" and frame.quarter and frame.year:
            return f"Q{frame.quarter} {g['relpy'] or _year_minus(frame.year)}"
        if frame.kind == "annual" and frame.year:
            return g["relpy"] or _year_minus(frame.year)
        return None  # a combined release's "prior year" could be the quarter or the year
    if g["bare"]:
        return g["bareyear"]
    return _NO  # a date — keep reading


def _clause(text: str, start: int, end: int, cap: int = 240) -> tuple[int, int]:
    """The figure's clause: back to the last sentence end, bullet or section heading, forward to
    the next. A HEADING is an edge because stripped HTML leaves none between a section's last
    bullet and the next heading — WERN's Q4 "…per share was $0.05, down 29% 2025 Highlights (all
    metrics compared to 2024)" otherwise hands the Q4 figure the next section's comparison."""
    lo_floor = max(0, start - cap)
    lo = lo_floor
    for e in _EDGE.finditer(text, lo_floor, start):
        lo = e.end()
    for h in _HEADING.finditer(text, lo, start):
        lo = max(lo, h.end())
    hi_cap = min(len(text), end + cap)
    nxt = _EDGE.search(text, end, hi_cap)
    hi = nxt.start() if nxt else hi_cap
    head = _HEADING.search(text, end, hi)
    return lo, (head.start(1) if head else hi)


def _outside_comparisons(text: str, lo: int, hi: int) -> list[re.Match[str]]:
    """Period phrases in [lo, hi) that do NOT sit inside a comparison sub-clause. MVST writes
    "Full Year net loss of $29.2 million, compared to net loss of $195.5 million in 2024; Non-GAAP
    adjusted net profit of $13.0 million" — the nearest year before the $13.0M is the COMPARISON's
    2024, and reading it would label a current full-year figure as the prior year."""
    cut: list[tuple[int, int]] = []
    for c in _CMP.finditer(text, lo, hi):
        stop = min((j for j in (text.find(";", c.end(), hi), text.find(". ", c.end(), hi))
                    if j != -1), default=hi)
        cut.append((c.start(), stop))
    return [p for p in _phrases(text, lo, hi) if not any(a <= p.start() < b for a, b in cut)]


def _heading_period(text: str, before: int, frame: _ReleaseFrame) -> object:
    """The period named by the nearest section heading above a figure, or ``_NO``."""
    heads = [h for h in _HEADING.finditer(text, max(0, before - 6000), before)
             if h.group(2) != "Results" or _PERIOD_WORD.search(h.group(1))]
    if not heads:
        return _NO
    words = heads[-1].group(1)
    names = _phrases(words, 0, len(words))
    if any(p.group("ytd") for p in names):
        return None  # "Year-to-Date Third Quarter Fiscal Year 2025 Summary" — a YTD section
    has_q = any(p.group("q") or p.group("qs") for p in names)
    has_fy = any(p.group("fy") for p in names)
    if has_q and has_fy and re.search(r"\band\b", words, re.I):
        return _NO  # "Fourth Quarter and Fiscal Year 2025 Highlights" — both periods, no answer
    for p in reversed(names):
        r = _as_current(p, frame)
        if r is not _NO:
            return r
    return _NO


def _comparison_at(text: str, lo: int, start: int) -> re.Match[str] | None:
    """The comparison marker that governs a figure, if the figure IS the compared value: the last
    marker in the figure's own clause with no other amount between it and the figure. Bounded to
    the clause on purpose — a 26-character look-back crossed a bullet and read SMPL's previous
    bullet ("$1.46 versus $1.33 •") as making its YTD adjusted EBITDA a prior-year comparison."""
    last = None
    for c in _CMP.finditer(text, lo, start):
        last = c
    if last is None or _AMOUNT.search(text, last.end(), start):
        return None
    return last


def _introduced(text: str, p: re.Match[str]) -> bool:
    return bool(_INTRO.search(text[max(0, p.start() - 24):p.start()]))


def _forward_looking(text: str, lo: int, start: int) -> bool:
    """True when the figure's own lead-in, or the lead-in of the bullet list it sits in, is an
    outlook. The list lead-in is the text from the last sentence end to the first bullet of the
    run the figure belongs to."""
    if _FORWARD.search(text, lo, start):
        return True
    sent = text.rfind(". ", max(0, lo - 1500), lo)
    sent = sent + 2 if sent != -1 else max(0, lo - 1500)
    first_bullet = re.search(r"[•●○◦■▪]", text[sent:lo])
    if not first_bullet:
        return False
    return bool(_FORWARD.search(text, sent, sent + first_bullet.start()))


def _period_order(label: str) -> tuple[int, int]:
    m = re.fullmatch(r"Q([1-4])\s+(20\d\d)", label)
    return (int(m.group(2)), int(m.group(1))) if m else (int(label), 4)


def _figure_period(text: str, start: int, end: int, frame: _ReleaseFrame, *,
                   comparison: bool | None = None) -> str | None:
    """The period ONE figure belongs to, from evidence about that figure. ``None`` means the text
    does not say, and the figure must not be labelled.

    Priority for a current figure: its own clause after the value (before any comparison, and only
    where a preposition introduces the period), its own clause before the value (comparison
    sub-clauses removed), the granularity its comparison clause implies, its section heading, and
    only then the header — and the header only when it names ONE period. A combined
    Q4-and-full-year header names two, so an unattributed figure under it is left unlabelled rather
    than filed as the year: that guess put BellRing's Q4 adjusted EBITDA of $117.4M, Concentrix's
    $378.6M and Uber's quarterly $2.5bn on their pages as FY2025.

    ``comparison`` overrides detection (tests); by default it is read from the clause itself."""
    lo, hi = _clause(text, start, end)
    marker = _comparison_at(text, lo, start)
    if comparison is None:
        comparison = marker is not None
    if comparison:
        stop = min((j for j in (text.find(";", end, hi),) if j != -1), default=hi)
        spans = ([(marker.end(), start)] if marker else []) + [(end, stop)]
        for a, b in spans:
            for p in _phrases(text, a, b):
                if a == end and not _introduced(text, p):
                    continue
                r = _as_prior(p, frame)
                if r is not _NO:
                    return r if isinstance(r, str) else None
        return None
    if _forward_looking(text, lo, start):
        return None
    label = _current_period(text, lo, hi, start, end, frame)
    if label and frame.kind in ("quarter", "combined", "annual") and frame.year:
        ceiling = (int(frame.year), frame.quarter or 4)
        if _period_order(label) > ceiling:
            return None  # an actual cannot postdate the release that reports it
    return label


def _current_period(text: str, lo: int, hi: int, start: int, end: int,
                    frame: _ReleaseFrame) -> str | None:
    cmp_at = _CMP.search(text, end, hi)
    for p in _phrases(text, end, min(cmp_at.start() if cmp_at else hi, end + 90)):
        if not _introduced(text, p):
            continue
        r = _as_current(p, frame)
        if r is not _NO:
            return r if isinstance(r, str) else None
    for p in reversed(_outside_comparisons(text, lo, start)):
        r = _as_current(p, frame)
        if r is not _NO:
            return r if isinstance(r, str) else None
    if cmp_at:
        stop = min((j for j in (text.find(";", cmp_at.end(), hi),) if j != -1), default=hi)
        for p in _phrases(text, cmp_at.end(), stop):
            r = _as_comparison_granularity(p, frame)
            if r is not _NO:
                return r if isinstance(r, str) else None
    h = _heading_period(text, lo, frame)
    if h is not _NO:
        return h if isinstance(h, str) else None
    if frame.kind == "quarter":
        return frame.label or None
    if frame.kind == "annual":
        return frame.year
    # No header period AND no year anywhere in it: the text carries no period information at all
    # (a bare excerpt), so there is nothing to be ambiguous ABOUT and the figure keeps the empty
    # label it always had — which neither consumer shape (Qn YYYY / YYYY) reads. A release that
    # DOES carry a year but cannot place this figure is skipped instead: its periods exist, and
    # a guess among them is the defect this resolver removes.
    return "" if frame.kind == "unknown" and not frame.year else None


# --- (1) non-GAAP reconciliation actuals ---------------------------------------------------------
# 'Non-GAAP adjusted EBITDA of positive $44.7 million' / '… of negative $5.5 million' / an adjusted
# net loss. NOT a guidance range: the (?! … to) tail rejects '… of $380 million to $385 million'.
_RECON = re.compile(
    # "Adjusted X" OR "Non-GAAP X" — filers use either, and EPAM/CNXC never write "adjusted"
    # ("Non-GAAP Diluted EPS of $3.26"). A footnote MARKER may follow the metric name: BellRing
    # writes "Adjusted EBITDA* of $53.8 million", and the un-tolerated '*' silently dropped the
    # whole release. \*? also covers the †/‡ conventions via the [*†‡]? class.
    #
    # THE PREFIX IS OPTIONAL FOR **EBITDA ALONE** (2026-09-18). Westlake names its reconciled
    # non-GAAP measure plainly — "EBITDA of $679 million for the second quarter of 2026" — so a
    # prefix-only rule read NOTHING from either of its 2026 releases and the page showed an empty
    # primary-source panel for a name whose EBITDA is the whole thesis. EBITDA is never a GAAP line
    # item, so a bare one is a non-GAAP figure by construction; net income, operating income and EPS
    # all have GAAP meanings and still REQUIRE the prefix — widening them would read a GAAP actual
    # as a non-GAAP one, which is the wrong-figure-under-a-familiar-name error `_norm_metric` exists
    # to refuse. The zero-width lookahead keeps the group numbering the caller reads.
    r"(?:(?:non-gaap|adjusted)\s+|(?=ebitda\b))"
    r"((?:diluted\s+)?(?:net\s+)?"
    r"(?:ebitda|income\s+from\s+operations|operating\s+income|net\s+(?:income|loss|profit)|"
    r"(?:income|loss)\s+per\s+share|earnings\s+per\s+share|eps))"
    # CONNECTOR: a verb ("of/was/totaled") OR a bare COLON — Gartner writes "adjusted EBITDA: $436
    # million, +5%" (period stated in the section header, not inline), which the verb-only connector
    # silently dropped. The currency-evidence + no-% guards below still gate every match, so a colon
    # can't admit a ratio ("adjusted EBITDA margin: 21%") or a non-amount.
    r"\s*[*†‡]?\s*(?::\s*|(?:of|was|totaled|of\s+approximately)\s+)"
    # CURRENCY EVIDENCE IS MANDATORY — a '$' before the number, or a million/billion after it.
    # Without this the pattern reads a RATIO as an amount: EPAM writes "non-GAAP income from
    # operations was 16.3% of revenues" (a margin), which was stored as $16.3M against a true
    # ~$230M on $1.4B revenue. A fabricated magnitude in a decision figure is the exact failure
    # this codebase refuses; a metric stated only as a percentage is simply not this extractor's.
    r"(positive\s+|negative\s+)?"
    r"(?:\$\s*([\d,.]+)\s*(?:million|billion)?|([\d,.]+)\s*(?:million|billion))"
    r"(?!\s*%)"
    r"(?!\s*(?:million\s+|billion\s+)?to\b)",
    re.I,
)
_GROSS_MARGIN = re.compile(
    r"gross\s+margin\s+(?:of\s+|(?:decreased|increased|declined)\s+to\s+|was\s+)?([\d.]+)\s*%",
    re.I,
)
# headline reported revenue (a GAAP actual, period-labeled) — the cross-source input for guide
# verification (a CIQ FY guide that merely echoes this prior-FY actual is a vendor artifact). The
# (?! … to) tail rejects a guidance range ('revenue of $985 million to $995 million').
_REVENUE = re.compile(
    r"(?:full[- ]year|total|quarterly|net)?\s*revenue\s+of\s+(?:a\s+record\s+)?"
    r"\$?\s*([\d,.]+)\s*(?:million|billion)(?!\s+to\b)",  # unit mandatory — else a greedy
    re.I,  # number backtracks to a truncated match ('98' ⊂ '985 million to')
)


#: A filer that writes BOTH "EBITDA" and "adjusted EBITDA" means two different measures by them.
_ADJ_EBITDA = re.compile(r"(?:non-gaap|adjusted)\s+ebitda", re.I)
_RECON_PREFIXED = re.compile(r"(?:non-gaap|adjusted)\s", re.I)


def _reconciliation(text: str, src: str, frame: _ReleaseFrame) -> list[ReconciliationValue]:
    """Non-GAAP actuals, headline revenue and GAAP gross margin — each labelled with the period
    ITS OWN text names (_figure_period), never the header's period by default.

    A figure whose period the release does not state is SKIPPED, not guessed. The two period
    shapes every consumer reads are ``Qn YYYY`` (a quarter) and a bare ``YYYY`` (a full year):
    ``_ltm_adj_ebitda`` composes LTM from them and ``_fy_reconciliation`` takes a bare year as the
    full-year margin input, so a quarter or a year-to-date figure wearing a bare year is not a
    labelling blemish — it is a wrong input to both, and to the synthesis that reads every row."""
    out: list[ReconciliationValue] = []
    seen: set[tuple[str, str]] = set()  # (metric, period) — current actual AND prior-year comp
    current = frame.label
    # A BARE "EBITDA" IS THE FILER'S NON-GAAP MEASURE ONLY WHERE THE FILER DRAWS NO DISTINCTION
    # (2026-09-18). Westlake writes "EBITDA of $679 million" and nothing else, so reading it is the
    # only way its page carries a non-GAAP figure at all. CF Industries writes BOTH in one sentence
    # — "EBITDA of $731 million, and adjusted EBITDA of $821 million" — and there the bare one is a
    # DIFFERENT measure: folding it into `adjusted ebitda` let $731M take the (metric, period) slot
    # and drop the real $821M, a different figure under a familiar name. Measured over the 91
    # releases the committed pages cite, exactly two state a bare "EBITDA of $" — both Westlake's —
    # and neither states an adjusted one, so this costs nothing live and closes the conflation.
    bare_ebitda_is_the_measure = _ADJ_EBITDA.search(text) is None

    def _segment(at: int) -> bool:
        # "The Commercial Services segment generated total revenue of $108.1 million" is one
        # segment, not the company — VRRM's Q4 page would have shown it as company revenue.
        lo, _ = _clause(text, at, at)
        return bool(re.search(r"\bsegments?\b", text[lo:at], re.I))

    # A comparison is the prior value OF the current figure in its own clause. If that clause's
    # current amount is NOT the value the release already stated for the same metric and period, the
    # clause is about a sub-unit, and its comparison is not the company's. WERN: "Werner Logistics
    # had a non-GAAP adjusted operating loss of $0.9 million, compared to Non-GAAP adjusted
    # operating income of $0.7 million in the prior year" follows the company's own "$27.6 million";
    # with the prior-year period now resolved, the segment's $0.7M would otherwise have stood as the
    # company's Q1-2025 figure. The test reads the AMOUNT, not the phrasing, so a current figure the
    # metric pattern cannot parse ("net profit per share of $0.05") still anchors its comparison.
    stated: dict[tuple[str, str], float] = {}

    def _sub_unit(lo: int, marker_start: int, metric: str) -> bool:
        eps = metric == "adjusted eps"
        amt = None
        for a in _LEAD_AMOUNT.finditer(text, lo, marker_start):
            if bool(a.group(2)) != (not eps):  # totals carry million/billion; EPS does not
                continue
            if _CHANGE_LEAD.search(text, max(lo, a.start() - 30), a.start()):
                continue  # "…$100.0 million, an increase of $10.0 million, compared to" — a delta
            amt = a
        if amt is None or (cv := _money(amt.group(1))) is None:
            return False
        cp = _figure_period(text, amt.start(), amt.end(), frame, comparison=False)
        prior = stated.get((metric, cp)) if cp else None
        # MAGNITUDES, not signs: a release writes a loss as "negative $5.5 million", "a loss of",
        # "$(5.5)" or "net loss", and reading the sign from the words got MVST's own restated
        # figure wrong. A sub-unit differs in SIZE (WERN: 0.9 against the company's 27.6).
        return prior is not None and abs(abs(prior) - cv) > max(0.005 * abs(prior), 1e-9)

    for m in _RECON.finditer(text):  # both captured, period-labeled, NEVER conflated
        # the amount comes from EITHER currency branch: "$53.8 million" (group 3) or
        # "53.8 million" (group 4). A bare number with neither marker no longer matches at all.
        metric_raw, sign = m.group(1), (m.group(2) or "").lower()
        num = m.group(3) or m.group(4)
        val, metric = _money(num), _norm_metric(m.group(1))
        if val is None or _segment(m.start()):
            continue
        if (metric == "adjusted ebitda" and not bare_ebitda_is_the_measure
                and _RECON_PREFIXED.match(m.group(0)) is None):
            continue  # this filer states an adjusted EBITDA too — the bare one is not it
        if "negative" in sign or "loss" in metric_raw.lower():
            val = -abs(val)
        lo, _ = _clause(text, m.start(), m.end())
        marker = _comparison_at(text, lo, m.start())
        if marker is not None and _sub_unit(lo, marker.start(), metric):
            continue
        p = _figure_period(text, m.start(), m.end(), frame, comparison=marker is not None)
        # a comparison can never share the release's own period (never conflate prior with current)
        if p is None or (marker is not None and p == current) or (metric, p) in seen:
            continue
        seen.add((metric, p))
        stated[(metric, p)] = val
        out.append(ReconciliationValue(
            metric=metric, period=p, value=val, change=_change_after(text, m.end()),
            verbatim=_verbatim(text, m.start(), m.end()), source_ref=src,
        ))
    for m in _REVENUE.finditer(text):  # headline revenue actual (same current/prior discipline)
        val = _money(m.group(1))
        if val is None or _segment(m.start()):
            continue
        lo, _ = _clause(text, m.start(), m.end())
        marker = _comparison_at(text, lo, m.start())
        if marker is not None and _sub_unit(lo, marker.start(), "revenue"):
            continue
        p = _figure_period(text, m.start(), m.end(), frame, comparison=marker is not None)
        if p is None or (marker is not None and p == current) or ("revenue", p) in seen:
            continue
        seen.add(("revenue", p))
        stated[("revenue", p)] = val
        out.append(ReconciliationValue(
            metric="revenue", period=p, value=val,
            verbatim=_verbatim(text, m.start(), m.end()), source_ref=src,
        ))
    gm = next((mm for mm in _GROSS_MARGIN.finditer(text)
               if "adjusted" not in text[max(0, mm.start() - 12):mm.start()].lower()), None)
    if gm and (v := _money(gm.group(1))) is not None:
        gp = _figure_period(text, gm.start(), gm.end(), frame)
        if gp is not None:
            out.append(ReconciliationValue(
                metric="gross margin", period=gp, value=v,
                verbatim=_verbatim(text, gm.start(), gm.end()), source_ref=src,
            ))
    return out


#: THE METRIC NAMES A GUIDANCE RANGE MAY BE ATTRIBUTED TO — ONE declaration, read by the range
#: pattern AND by the ambiguity refusal below. They were two literals; a metric the range pattern
#: could attribute but the refusal could not see is a shared-range sentence silently given to one of
#: two candidates, so they are the same string or they are a bug waiting.
#:
#: HELD AT THE NAMES IT ALREADY CARRIED, and that is a decision with a measurement behind it
#: (2026-09-18). Adding `operating income` and the prefix-free per-share forms extracts 22 more
#: real ranges across the fleet — Amazon's operating-income guide, EPAM's GAAP diluted EPS,
#: Concentrix's and nCino's operating income, Uber's non-GAAP EPS — and EVERY ONE of them states
#: its period in a bullet-list header the clause cannot reach, so all 22 land on the `next-fy`
#: default, which `period_scope` reads as ANNUAL. A quarterly guide wearing an annual label is a
#: ~4x error in a decision figure, and more rows are not worth it. The gap is recorded, with its
#: 22 witnesses, in docs/records/2026-09-18-release-parse-fleet-audit.md.
_GUIDE_METRICS = (
    r"total\s+revenues?|net\s+sales|revenues?|adjusted\s+ebitda|adjusted\s+eps|"
    r"adjusted\s+earnings\s+per\s+share|free\s+cash\s+flow|gross\s+margin"
)


# --- (2) guidance ranges + QUALITATIVE-only outlook ----------------------------------------------
_GUIDE_RANGE = re.compile(
    # Metric names as filers write them (net sales / total revenues — BellRing, Simply Good, nCino
    # all guide on these and were invisible), an optional footnote marker, and BOTH range
    # phrasings: "outlook of $X to $Y" and "expected to range between $X and $Y".
    # OPERATING INCOME and a prefix-free DILUTED EPS joined the vocabulary 2026-09-18: Amazon guides
    # "Operating income is expected to be between $22.5 billion and $27.5 billion" — the most-read
    # number in that release — and EPAM guides "diluted EPS will be in the range of $2.33 to $2.41".
    # The adjusted-diluted variants are listed FIRST so a match starts at "adjusted", not inside it:
    # `re` is leftmost-first, and a match beginning at "diluted" would lose the prefix and relabel a
    # non-GAAP guide as a GAAP one.
    rf"(?P<metric>{_GUIDE_METRICS})"
    # Artivion writes "revenues FOR THE FULL YEAR 2026 TO BE in the range of $486 to $504 million";
    # the old pattern required the introducer to follow the metric immediately, so a real, numeric,
    # in-sentence range was invisible and fell through to the qualitative marker.
    #
    # The interlude is SPELLED OUT rather than left as a wildcard gap, and that is not fussiness:
    # a `[^.$•]{0,60}?` gap was tried first and the per-item table over all 51 caught it binding a
    # metric to a number from a LATER clause — VITL's revenue guide took the adjusted-EBITDA range
    # (900–920 became 105–115) and EPAM's took a prior year's (4.5–7.5 became 14.8–15.2). It also
    # moved the match start, which shifted `_period_near`'s window and dropped the year off eight
    # otherwise-correct items. A wildcard between a metric and its number is the same
    # wrong-magnitude class this whole item exists to remove.
    r"\s*[*†‡]?\s*(?:for\s+the\s+full\s+year(?:\s+20\d\d)?\s+)?"
    # THE AUXILIARY IS A SLOT, NOT A GAP (2026-09-18). The introducer had to follow the metric
    # almost immediately, so the most ordinary English shape a filer uses was invisible: "Net sales
    # ARE EXPECTED TO BE between $197.0 billion and $202.0 billion" (Amazon, both 2026 releases) and
    # "revenues WILL BE in the range of $1.410 billion" (EPAM, nine statements). Measured over the
    # 91 releases the committed pages cite, those two shapes are the whole of the guidance miss.
    # Spelled out, never `[^.]{0,40}?`: a wildcard here is what bound VITL's revenue guide to the
    # adjusted-EBITDA range one clause later, and the same trap is one character away.
    r"(?:(?:(?:is|are|was|were)\s+(?:now\s+)?)?"
    r"(?:expected|anticipated|projected|forecast(?:ed)?)\s+|will\s+be\s+)?"
    r"(?:to\s+be\s+)?"
    # "…expected to range FROM $52 million to $56 million" (Simply Good) is the same range, stated
    # with the other preposition.
    r"(?:outlook\s+of|expected\s+to\s+range\s+(?:between|from)|to\s+range\s+(?:between|from)|"
    r"in\s+the\s+range\s+of|between|of)\s+"
    # range separator: "to" / "and" / a bare hyphen or en/em dash ("$2.325-$2.365 billion" —
    # BellRing). The dash form carries no spaces, so \s* around it, not \s+.
    # `pct` is CAPTURED now: it used to be discarded inside a non-capturing group, so a percentage
    # range was stored with the default "$M" unit.
    # UNIT SUFFIXES ARE UNITS (2026-08-12). Filers write the magnitude two ways and only the
    # spelled-out word was read: NFLX guides "2026 revenue of $50.7-$51.7B" and "$50.7B-$51.7B" in
    # the same exhibit. The suffix form failed THREE ways at once — a trailing `B` was ignored
    # (50.7 stood for $50.7M, a 1000x understatement of a $50bn guide), and a LEADING one broke the
    # match entirely because `B` sat where the separator had to be, so the guide was dropped with no
    # flag. `bn`/`mm` are the same family. The single letters carry `(?![A-Za-z])` because `[MB]`
    # under re.I otherwise eats the first letter of the next word — "$2.4 to $2.5 based on…" would
    # read `b`("based") as billions, which is the magnitude error this is fixing, inverted.
    #
    # THE LOW SIDE'S UNIT IS CAPTURED, not discarded, and that is a second defect fixed here: the
    # trailing unit was applied to BOTH numbers, so "$500 million to $1.2 billion" scaled the low
    # side by 1000 and produced low=500,000 against high=1,200 — a range whose floor sits 400x above
    # its ceiling. Each side now scales by ITS OWN stated unit; a bare side inherits the trailing
    # one (unchanged for "$2.465 to $2.49 billion", where only the trailing unit is stated).
    r"\$?\s*(?P<low>[\d,.]+)\s*(?P<pct>%)?\s*"
    r"(?:(?P<lowunit>million|billion|bn|mm|[MB])(?![A-Za-z])\s*)?"
    r"(?:to|and|[-–—])\s*"
    r"\$?\s*(?P<high>[\d,.]+)\s*"
    r"(?:(?P<unitword>million|billion|bn|mm|[MB]|%)(?![A-Za-z]))?",
    re.I,
)


#: Scale a stated magnitude word/suffix onto the ``$M`` the composer prints. Anything unrecognised
#: (or absent) is 1.0 — a guessed magnitude is the fabrication this codebase refuses, so an unknown
#: unit leaves the number as filed rather than inventing a multiplier for it.
def _unit_scale(word: str | None) -> float:
    w = (word or "").strip().lower()
    return 1000.0 if (w.startswith("billion") or w in {"bn", "b"}) else 1.0
# A GROWTH-RATE guide is a real number, not a qualitative outlook: EPAM guides
# "the year-over-year revenue growth rate to be in the range of 4.5% to 7.5%". The dollar-range
# pattern cannot see it, so it fell through to the QUALITATIVE marker — which asserts the company
# said nothing when it said the most decision-relevant thing in the release.
_GUIDE_PCT = re.compile(
    r"(revenue|net\s+sales|total\s+revenues?|adjusted\s+ebitda|gross\s+margin)"
    r"[^.]{0,60}?growth\s+rate[^.]{0,60}?"
    r"(?:in\s+the\s+range\s+of|between|of)\s+"
    r"([\d.]+)\s*%\s*(?:to|and|[-–—])\s*([\d.]+)\s*%",
    re.I,
)
# --- CHANGE-BASIS GUIDES (2026-08-05) -----------------------------------------------------------
# A guide can state a LEVEL the metric reaches or a CHANGE from the prior period, and until now
# only the first was expressible. Ten of seventeen dropped clauses across four names were changes:
# SMPL alone guides gross margin as a basis-point decline in every release, which is the metric its
# own kill criteria test. The metric ALLOWLIST was never the problem — `gross margin` has always
# been in it; the SHAPE was.
#
# FOUR SHAPES, each with a live example, and the plural is not cosmetic: `gross\s+margin` followed
# by `\s*` cannot consume the `s` in "Gross margins", so SMPL's guide failed to match on the noun
# alone before any of the rest mattered.
#
#   "Gross marginS expected to decline between 300 and 350 basis points"   two-sided, bps
#   "Gross marginS expected to decline approximately 375 basis points"     one-sided, bps
#   "Net sales expected to range between -2% and +2% year-over-year"       two-sided, signed %
#   "Adjusted EBITDA expected to increase 4% to 5%"                        two-sided, % change
#
# THE DIRECTION WORD CARRIES THE SIGN, and it must: "decline 375 bps" stored as +375 is the same
# 100x-class error as storing it as a level. `_DECLINE` words negate; `_RISE` words do not.
_METRIC_ALT = (r"total\s+revenues?|net\s+sales|revenues?|adjusted\s+ebitda|adjusted\s+eps|"
               r"adjusted\s+earnings\s+per\s+share|free\s+cash\s+flow|gross\s+margins?")
_DIRECTION = r"(?P<dir>decline|decrease|contract|improve|increase|expand|grow|rise)"
_DECLINE = {"decline", "decrease", "contract"}
# a CHANGE range: "…decline between 300 and 350 basis points" / "…increase 4% to 5%"
_GUIDE_CHANGE_RANGE = re.compile(
    rf"(?P<metric>{_METRIC_ALT})\s*[*†‡]?\s*"
    rf"(?:expected\s+to\s+|to\s+)?{_DIRECTION}\s+"
    r"(?:by\s+)?(?:in\s+a\s+range\s+of\s+|in\s+the\s+range\s+of\s+|between\s+)?"
    r"(?P<low>[\d,.]+)\s*(?P<lowunit>%|basis\s+points|bps)?\s*(?:to|and|[-–—])\s*"
    r"(?P<high>[\d,.]+)\s*(?P<unitword>%|basis\s+points|bps)",
    re.I,
)
# a SINGLE-POINT change: "…decline approximately 375 basis points" / "…decline by ~200 bps"
_GUIDE_CHANGE_POINT = re.compile(
    rf"(?P<metric>{_METRIC_ALT})\s*[*†‡]?\s*"
    rf"(?:expected\s+to\s+|to\s+)?{_DIRECTION}\s+"
    r"(?:by\s+)?(?:approximately|about|roughly|~)?\s*"
    r"(?P<low>[\d,.]+)\s*(?P<unitword>%|basis\s+points|bps)",
    re.I,
)
# a SIGNED two-sided change: "expected to range between -2% and +2% year-over-year". No direction
# word — the signs carry it — so this cannot share the pattern above.
_GUIDE_CHANGE_SIGNED = re.compile(
    rf"(?P<metric>{_METRIC_ALT})\s*[*†‡]?\s*"
    r"(?:expected\s+to\s+range\s+between|to\s+range\s+between|expected\s+to\s+be\s+between)\s+"
    r"(?P<low>[+-][\d,.]+)\s*(?P<lowunit>%)\s*(?:to|and|[-–—])\s*"
    r"(?P<high>[+-][\d,.]+)\s*(?P<unitword>%)",
    re.I,
)


def _change_unit(word: str | None) -> str:
    """`bps` for a basis-point guide, `%` otherwise — never the `$M` default, which is what a
    change guide stored under the level vocabulary would silently claim."""
    w = (word or "").strip().lower()
    return "bps" if w in ("basis points", "bps") else "%"


def _signed(value: float, direction: str | None) -> float:
    """A decline is NEGATIVE. Storing "decline 375 bps" as +375 is the same class of error as
    storing it as a level — the number would read as an expansion."""
    return -abs(value) if (direction or "").lower() in _DECLINE else value


_OUTLOOK = re.compile(
    r"(20\d\d\s+outlook|financial\s+outlook|revised\s+(?:its\s+|full[- ]year\s+)?(?:financial\s+)?"
    r"outlook|(?:full[- ]year\s+)?guidance\s+for\s+20\d\d)",
    re.I,
)


def _guide_metric(raw: str) -> str:
    r = raw.lower()
    if "revenue" in r:
        return "revenue"
    if "ebitda" in r:
        return "adjusted ebitda"
    if "eps" in r or "per share" in r:
        return "adjusted eps"
    if "cash flow" in r:
        return "free cash flow"
    if "margin" in r:
        return "gross margin"
    return r.strip()


#: THE SAME METRIC VOCABULARY AS `_GUIDE_RANGE`, and it must stay that way: this is what the
#: ambiguity refusal counts, so a metric the range pattern can attribute but this cannot see is a
#: metric whose shared-range sentence is silently attributed to one of two candidates.
_METRIC_WORDS = re.compile(_GUIDE_METRICS, re.I)
# The prefix a guidance REFUSAL carries. Shared so the rollup in `vinci.dossier.mechanical`
# selects on the same literal that is emitted here, rather than on a copy that can drift.
GUIDANCE_REFUSAL_PREFIX = "Guidance stated but not attributable"
_QUARTER = re.compile(r"\b(first|second|third|fourth)\s+quarter\b", re.I)
_Q_NUM = {"first": 1, "second": 2, "third": 3, "fourth": 4}
# A forward statement ABOUT THE BUSINESS. "updated its financial outlook" is a statement about the
# ACT of guiding and says nothing forward — Gartner's boilerplate opener matched `_OUTLOOK` on
# exactly that phrase and produced two fabricated revenue guides from a sentence that carries no
# outlook at all. Microvast's real qualitative outlook says "we anticipate a recovery".
_FORWARD_VERB = re.compile(
    r"\b(?:expects?|expecting|anticipates?|anticipating|forecasts?|projects?|targets?|"
    r"sees|continues?\s+to\s+(?:expect|see))\b", re.I)


def _guide_unit(metric: str, pct_marker: str | None) -> str:
    """The unit a guidance range is stated in — DERIVED, never assumed (2026-07-29).

    Order matters: an explicit '%' in the text wins, because a percentage guide is a percentage
    whatever the metric; then a per-share metric is ``$/sh``; otherwise ``$M``. There was no
    branch for the middle case at all, which is why VRRM's $1.19–$1.25 EPS guide rendered in
    millions. See ``GUIDANCE_UNITS``."""
    if pct_marker:
        return "%"
    if metric == "adjusted eps":
        return "$/sh"
    if metric == "gross margin":
        return "%"
    return "$M"


def _period_for(text: str, start: int, end: int, verbatim: str) -> str:
    """The period a guide governs, read from the guide's OWN sentence first.

    Two live defects came from reading it elsewhere. FUBO's bullet says "Fiscal 2026 Pro Forma
    Adjusted EBITDA of $80-100 million" and was labelled **Fiscal 2028** — the forward scan crossed
    into a later bullet. Concentrix guides a QUARTER ("Third quarter reported revenue of $2.465
    billion to $2.490 billion") and was labelled **Fiscal 2026**, turning a quarterly range into a
    full-year one on a business annualising ~$9.9bn.

    So the enclosing bullet/sentence governs, and a quarter named there BEATS a bare year: a
    quarterly range mislabelled annual is a ~4x error in a decision figure."""
    q = _QUARTER.search(verbatim)
    y = _PERIOD.search(verbatim)
    if q is not None:
        yr = re.search(r"20\d\d", y.group(1)) if y else None
        return f"Q{_Q_NUM[q.group(1).lower()]}" + (f" {yr.group(0)}" if yr else "")
    if y is not None:
        return re.sub(r"\s+", " ", y.group(1)).strip()
    # THE REST OF THE CLAUSE, CUT AT THE COMPARISON (2026-09-18). `_verbatim` snaps BACKWARD to the
    # bullet start and stops at the match, so a period stated just AFTER the range was unreachable:
    # EPAM's "revenues will be in the range of $1.410 billion to $1.425 billion FOR THE THIRD
    # QUARTER" fell through to `next-fy`, and `period_scope` reads that as ANNUAL — which would put
    # a $1.4bn quarterly range against a full-year CIQ guide on a ~$5.6bn business and report the
    # 4x as a cross-source mismatch instead of refusing the comparison.
    #
    # The cut is what keeps the tail honest: Amazon writes "Operating income is expected to be
    # between $22.5 billion and $26.5 billion, COMPARED WITH $17.4 billion in third quarter 2025",
    # and the only period within reach of that guide belongs to the period it is measured against.
    # A forward guide wearing a closed period is worse than an unlabelled one.
    # A TRAILING PERIOD COUNTS ONLY WHERE A PREPOSITION INTRODUCES IT — `_introduced`, the guard
    # `_phrases` already applies for the same reason. Without it the scan walks straight out of the
    # guide and into the next sentence: Simply Good's FY range "…$220 to $225 million, or -21% to
    # -19% year-over-year" is followed by the CEO quote "Our THIRD QUARTER results reflect…", and an
    # unguarded tail labelled a full-year guide a quarter — a ~4x error, the exact shape of the
    # Concentrix defect above, arrived at from the other end.
    lo, hi = _clause(text, start, end)
    cut = _CMP.search(text, end, hi)
    tail_hi = cut.start() if cut is not None else hi
    tq = next((x for x in _QUARTER.finditer(text, end, tail_hi) if _introduced(text, x)), None)
    ty = next((x for x in _PERIOD.finditer(text, end, tail_hi) if _introduced(text, x)), None)
    if tq is None and ty is None:
        # the LEAD-IN, which is where a bullet list states the period once for the bullets under it
        # ("Third Quarter 2026 Guidance • Net sales are expected to be between…"). Quarter-first for
        # the same reason as the verbatim: a quarterly range wearing an annual label is the error.
        back = max(0, start - 60)
        tq, ty = _QUARTER.search(text, back, start), _PERIOD.search(text, back, start)
    if tq is not None:
        yr = re.search(r"20\d\d", ty.group(1)) if ty else None
        return f"Q{_Q_NUM[tq.group(1).lower()]}" + (f" {yr.group(0)}" if yr else "")
    if ty is not None:
        return re.sub(r"\s+", " ", ty.group(1)).strip()
    return "next-fy"


def _guidance(text: str, src: str, notes: list[str] | None = None) -> list[GuidanceItem]:
    """Guidance items from a release. ``notes`` collects REFUSALS — sentences that plainly state a
    guidance range which cannot be attributed safely.

    A REFUSAL MUST NOT BE SILENT (item 22). "We found guidance and could not parse it" is a
    different fact from "this release states no guidance", and a reader whose guidance picture is
    incomplete needs to know which one they have. The existing ``no anchored pattern matched`` flag
    already covers the second; before this, the first vanished entirely — leaving no trace that a
    number had been seen and declined, which is the absent-and-silent shape the rule prohibits."""
    out: list[GuidanceItem] = []
    seen: set[str] = set()
    notes = notes if notes is not None else []
    for m in _GUIDE_RANGE.finditer(text):
        metric = _guide_metric(m["metric"])
        low, high = _money(m["low"]), _money(m["high"])
        if low is None or high is None or metric in seen:
            continue
        vb = _verbatim(text, m.start(), m.end())
        # AMBIGUOUS SENTENCE ⇒ REFUSE, never guess. BellRing writes "Fiscal year 2026 net sales and
        # Adjusted EBITDA* expected to range between $2.41-$2.49 billion": TWO metrics, ONE range.
        # The regex binds it to whichever sits nearer the introducer, which produced an "adjusted
        # EBITDA" guide of $2,410–2,490M against a business earning ~$490M — a ~5x error stated
        # confidently. A reader cannot resolve that sentence either, so neither may we — but the
        # refusal is ATTRIBUTED, with the sentence, so the reader can resolve it from the filing.
        named = {_guide_metric(x.group(0)) for x in _METRIC_WORDS.finditer(vb)}
        if len(named) > 1:
            notes.append(
                f"{GUIDANCE_REFUSAL_PREFIX} — one range is shared by "
                f"{len(named)} metrics ({', '.join(sorted(named))}), so which it governs cannot be "
                f"read from the sentence; verify against the filing: \"{vb[:150]}\" ({src})")
            continue
        # UNITS: normalise to $M. Concentrix guides revenue in BILLIONS ("$2.465 to $2.49 billion")
        # while every other name guides in millions, and the composer prints the bare number — so an
        # un-scaled 2.465 read as $2.5M beside VRRM's 985.0 ($M). A magnitude error in a
        # decision figure is worse than an absent one, so scale here where the unit word is in hand.
        # Scale ONLY on the stated unit word — the trailing unit governs the whole range
        # ("$2.465 to $2.49 billion"). Inferring billions from magnitude would be a guess, and a
        # guessed magnitude is exactly the fabrication this codebase refuses.
        unit = _guide_unit(metric, m["pct"] or (m["unitword"] if m["unitword"] == "%" else None))
        if unit == "$M":
            # PER-SIDE, with the trailing unit as the fallback for a bare side. "$2.465 to $2.49
            # billion" states one unit and it governs both (unchanged); "$500 million to $1.2
            # billion" states two and each governs its own number.
            governing = m["unitword"] or m["lowunit"]
            low *= _unit_scale(m["lowunit"] or governing)
            high *= _unit_scale(m["unitword"] or governing)
        # AN IMPOSSIBLE RANGE ⇒ REFUSE, AND DO NOT SORT IT (review finding, #430). Per-side scaling
        # is what makes this reachable: "$1.2 billion to $500M" arrives as low=1,200 high=500, and
        # before this it was emitted as real guidance — printed on the page and fed to the
        # cross-check. SORTING IS THE WRONG REPAIR: it would state 500–1,200 as the filing's range
        # when the filing said the reverse, and if the true cause is a mis-parse (the unit words
        # bound to the wrong sides) it hides the evidence of that instead of surfacing it.
        # DIFFERENT FROM THE CHANGE-BASIS SWAP one loop down, which DOES sort: there the inversion
        # is a mechanical consequence of applying a sign (a decline range signs to -350..-300), not
        # an anomaly in what was written. Here nothing mechanical produced it.
        # PROTECTIVE, NOT CORRECTIVE — measured across every committed dossier: 56 guidance items
        # carry both bounds and NONE is inverted, so no live page changes.
        if low > high:
            notes.append(
                f"{GUIDANCE_REFUSAL_PREFIX} — the stated range runs backwards after unit "
                f"normalisation ({low:,.1f} to {high:,.1f} {unit}), so the bounds cannot be read "
                f"with confidence; verify against the filing: \"{vb[:150]}\" ({src})")
            continue
        seen.add(metric)
        out.append(GuidanceItem(
            metric=metric, period=_period_for(text, m.start(), m.end(), vb),
            low=low, high=high, unit=unit, qualitative=False,
            verbatim=vb, source_ref=src,
        ))
    for m in _GUIDE_PCT.finditer(text):
        metric = _guide_metric(m.group(1))
        lo, hi = _money(m.group(2)), _money(m.group(3))
        if lo is None or hi is None or metric in seen:
            continue
        vb = _verbatim(text, m.start(), m.end())
        # A DECLINE WORD MAKES THE SIGN AMBIGUOUS ⇒ REFUSE, never guess — the BellRing precedent
        # one loop up. "the revenue growth rate to decline in the range of 2% to 3%" reads two ways:
        # the growth rate DECLINES TO +2..+3% (positive), or it declines BY 2..3% (negative). This
        # pattern captures bare digits and would store +2.0..+3.0 either way.
        #
        # That only became load-bearing when this path started claiming `basis="change"`: a sign is
        # what a change MEANS, and "a decline stored positive reads as an expansion" is the error
        # class `test_guidance_change_basis` already exists to prevent. `_GUIDE_CHANGE_RANGE` reads
        # the SAME word as unambiguously negative (`_DECLINE`), so accepting it positive here would
        # put two parsers of one concept in contradiction — and this one runs FIRST and would
        # shadow the other through `seen`. Refusing leaves the sentence to them, or to the reader.
        if any(w in vb.lower() for w in _DECLINE):
            notes.append(
                f"{GUIDANCE_REFUSAL_PREFIX} — a growth-rate range stated with a decline word: "
                f"\"{vb[:150]}\" reads either as declining TO that range or BY it, and the two "
                f"have opposite signs; verify against the filing ({src})")
            continue
        seen.add(metric)
        # `basis="change"`, and the pattern is what makes that SAFE rather than a guess:
        # `_GUIDE_PCT` requires the literal `growth rate` within 60 chars of the metric, so every
        # match is a rate of change BY CONSTRUCTION. A `%` figure alone would be ambiguous — "gross
        # margin expected to be 29% to 30%" is a LEVEL in percent — but that sentence cannot reach
        # here, because it says no "growth rate".
        #
        # WHAT THE WRONG LABEL COST. EPAM's `revenue` carried BOTH `4.0–6.5 %` and
        # `5430.0–5445.0 $M`, both stamped "level". PR 2's cross-basis refusal is gated on
        # `release_basis == "change"`, so it never fired, and `guide_verification` compared a
        # QUARTERLY LEVEL IN $M against a FULL-YEAR GROWTH RATE IN PERCENT:
        #     "guide verification (revenue): CIQ 1400.0–1415.0 vs release 4.0–6.5 → MISMATCH flag"
        # The synthesis then wrote a bear point on that MISMATCH — a fabricated signal reaching the
        # decision surface. PR 2 fixed the COMPARE; the label is what let a change through it.
        out.append(GuidanceItem(
            metric=metric, period=_period_for(text, m.start(), m.end(), vb),
            low=lo, high=hi, unit="%", basis="change", qualitative=False,
            verbatim=vb, source_ref=src,
        ))
    # CHANGE-BASIS GUIDES, AFTER the level patterns and gated on `seen`, so a metric that stated a
    # LEVEL keeps it: a level is the stronger statement and a release that gives both (SMPL gives
    # net sales as a level AND gross margin as a change) must not have the level overwritten. The
    # three patterns run most-specific first — a two-sided range before a single point, or
    # "between 300 and 350" would match the point pattern on "300" alone and drop the high end.
    for pat, two_sided in ((_GUIDE_CHANGE_SIGNED, True), (_GUIDE_CHANGE_RANGE, True),
                           (_GUIDE_CHANGE_POINT, False)):
        for m in pat.finditer(text):
            metric = _guide_metric(m["metric"])
            if metric in seen:
                continue
            lo = _money(m["low"])
            hi = _money(m["high"]) if two_sided else lo
            if lo is None or hi is None:
                continue
            unit = _change_unit(m.groupdict().get("unitword"))
            direction = m.groupdict().get("dir")
            lo, hi = _signed(lo, direction), _signed(hi, direction)
            if lo > hi:                      # a decline range reverses: -350..-300, not -300..-350
                lo, hi = hi, lo
            vb = _verbatim(text, m.start(), m.end())
            seen.add(metric)
            out.append(GuidanceItem(
                metric=metric, period=_period_for(text, m.start(), m.end(), vb),
                low=lo, high=hi, unit=unit, basis="change", qualitative=False,
                verbatim=vb, source_ref=src,
            ))

    # QUALITATIVE-only: an outlook section that names revenue but carries NO number in its window.
    om = _OUTLOOK.search(text)
    if om and "revenue" not in seen:
        window = text[om.start():om.start() + 700]
        # (Artivion's numeric range now matches `_GUIDE_RANGE` via the interlude above, so it
        # never reaches this fallback; the fallback is left exactly as it was.)
        has_rev_number = re.search(r"revenue\D{0,40}\$\s*[\d,]", window, re.I)
        vb = _verbatim(text, om.start(), om.start() + 200)
        # BOILERPLATE IS NOT AN OUTLOOK. Gartner's opener — "(NYSE: IT) today reported results for
        # the first quarter of 2026 and updated its financial outlook for the full year 2026" —
        # matches `_OUTLOOK` on the phrase "financial outlook" while stating no outlook whatever.
        # It fabricated two revenue guides. Require a forward statement about the BUSINESS, and
        # reject the results-announcement opener however many outlook words it carries.
        forward = _FORWARD_VERB.search(window)
        if re.search(r"revenue", window, re.I) and not has_rev_number and forward:
            ym = re.search(r"20\d\d", om.group(1))
            out.append(GuidanceItem(
                metric="revenue", period=ym.group(0) if ym else "next-fy",
                low=None, high=None, qualitative=True,
                verbatim=vb, source_ref=src,
            ))
    return out


# --- (3) one-off items (impairments / charges) ---------------------------------------------------
_ONEOFF = re.compile(
    # The one-off IS usually the reason for the gap ("a pre-tax $11.3 million inventory-related
    # charge"), so the noun set must cover how filers actually write it — charge / costs /
    # expenses, not only impairment-family words. Each generic noun REQUIRES a qualifier before it
    # (restructuring, integration, one-time, inventory-related …) so routine operating costs
    # ("cost of goods sold", "interest expense") are never mistaken for a discrete item.
    r"\$\s*([\d,.]+)\s*(?:million|billion)\s+(?:of\s+|in\s+)?"
    r"((?:[\w'’-]+\s+){0,6}?"
    r"(?:impairment|write[- ]?off|write[- ]?down|"
    r"(?:restructuring|integration|one[- ]?time|transaction|acquisition[- ]related|"
    r"inventory[- ]related|impairment[- ]related|separation|transition|legal\s+settlement)"
    r"\s+(?:charge|charges|cost|costs|expense|expenses))"
    r"[\w\s,'’-]{0,80})",
    re.I,
)


def _one_offs(text: str, src: str) -> list[OneOffItem]:
    by_key: dict[str, OneOffItem] = {}
    # key → normalized FULL raw desc, for the identical-item (same-scope-two-figures) collapse
    raw_by_key: dict[str, str] = {}
    for m in _ONEOFF.finditer(text):
        amt = _money(m.group(1))
        if amt is None:
            continue
        raw_desc = " ".join(m.group(2).split())
        # trim at the next clause boundary AND at the first comma — a one-off's name rarely spans a
        # comma, so the comma introduces a SECOND, different item ("restructuring costs, integration
        # expenses of" → "restructuring costs", not a fragment dangling at "of").
        desc = re.split(r"(?:,\s|\.\s|;\s|\s+which\b)", raw_desc)[0][:200].strip()
        # belt-and-braces: never end on a bare preposition/conjunction
        desc = re.sub(r"\s+(?:of|in|for|to|by|and|the|a|an)$", "", desc, flags=re.I).strip()
        # PRIOR-PERIOD COMPARATIVES are not this period's one-off. A release states the current
        # charge and then restates last year's beside it ("and for the prior year period
        # integration expenses of $0.2 million"); listing both as drivers of THIS gap-down would
        # attribute a year-old item to today's move.
        # Look back only to the START OF THIS SENTENCE — a fixed character window reaches across
        # sentence boundaries and kills a current-period item merely because the preceding
        # sentence mentioned last year ("Compared with the prior year period, results improved.
        # The quarter included a $25.0 million impairment charge.").
        sent_start = max(text.rfind(". ", max(0, m.start() - 300), m.start()),
                         text.rfind("• ", max(0, m.start() - 300), m.start()))
        window = text[(sent_start + 1) if sent_start != -1 else max(0, m.start() - 90):m.start()]
        if re.search(r"prior[- ]year|prior\s+period|year[- ]ago", window, re.I):
            continue
        if re.match(r"^(?:and\s+)?(?:for|in)\b", desc, re.I):  # a dangling comparative fragment
            continue
        # ONE ROW PER DISTINCT ITEM. A press release repeats the same charge in the highlights and
        # again per segment, at different roundings ($11 million / $11.3 million), so a bare dedup
        # on the exact string leaves eight copies of one fact. Key on the item's NOUN PHRASE and
        # keep the most precise mention (the largest magnitude wins ties of rounding).
        # ONE ROW PER DISTINCT ITEM — but "distinct" needs the AMOUNT too. Keying on the noun
        # phrase alone collapsed two genuinely different charges ($12.0M European footprint and
        # $30.0M Asia exit both read "restructuring charges rel…"), silently dropping the smaller.
        # Same phrase AND a near-equal amount is one item restated at a different rounding
        # ($11.0M / $11.3M); a materially different amount is a different item.
        phrase = re.sub(r"[^a-z ]", "", desc.lower())[:24].strip()
        # default key CARRIES THE AMOUNT, so two different charges under the same phrase stay two
        # rows; the loop below re-uses an existing key when the amounts are near-equal (one item
        # restated at a different rounding, $11.0M/$11.3M) OR when the FULL raw descriptions are
        # byte-identical (the SAME item quoted at two reconciliation scopes — SMPL's OWYN
        # integration expense at $3.9M for the quarter and $6.5M year-to-date, both worded
        # identically). A DIFFERENT qualifier ($12M European vs $30M Asia restructuring) keeps two.
        raw_norm = re.sub(r"[^a-z ]", "", raw_desc.lower())[:60].strip()
        key = f"{phrase}|{amt}"
        for k, seen_item in by_key.items():
            same_rounding = k.startswith(phrase[:16]) and _near(amt, seen_item.amount)
            same_item = raw_by_key.get(k) == raw_norm
            if same_rounding or same_item:
                key = k
                break
        prev = by_key.get(key)
        # keep the FIRST occurrence for an identical-item collapse (the quarter is quoted first, and
        # the gap-down driver wants the QUARTER figure); a same-phrase non-identical mention is a
        # rounding tie ($11.0M/$11.3M) where the more precise (larger/longer) wins. ACCEPTED RISK:
        # two GENUINELY DIFFERENT charges worded byte-identically in the captured phrase (differing
        # only in amount, no distinguishing scope/qualifier text — indistinguishable from SMPL's
        # same-item QTD/YTD restatement) collapse to the first; recorded in STATE.md with its
        # falsifier. No local signal separates the two, so the code optimizes for the observed case.
        identical_item = raw_by_key.get(key) == raw_norm
        if prev is None or (not identical_item and (amt > prev.amount
                            or (amt == prev.amount and len(desc) > len(prev.description)))):
            by_key[key] = OneOffItem(
                amount=amt, description=desc,
                verbatim=_verbatim(text, m.start(), m.end()), source_ref=src,
            )
            raw_by_key[key] = raw_norm
    return list(by_key.values())


# --- (4) event-impact quantifications (the Avis class) -------------------------------------------
# 'reduce Commercial Services' 2026 annualized revenue by approximately $135 million to $145 million
#  and 2026 annualized segment profit by approximately $120 million to $125 million' — the 'reduce'
# governs both legs; the second inherits the direction (no 'reduce' of its own).
_IMPACT = re.compile(
    r"([\w'’\s]{0,60}?)\s+by\s+approximately\s+\$?\s*([\d,.]+)\s*(?:million|billion)?\s+to\s+"
    r"\$?\s*([\d,.]+)",
    re.I,
)
_DIR_BACK = re.compile(r"(reduc\w*|lower\w*|decreas\w*|increas\w*|rais\w*|improv\w*)", re.I)


def _impact_metric(phrase: str) -> str:
    r = phrase.lower()
    if "segment profit" in r:
        return "segment profit"
    if "revenue" in r:
        return "revenue"
    if "ebitda" in r:
        return "ebitda"
    if "eps" in r or "per share" in r:
        return "eps"
    return r.strip()


def _event_impacts(text: str, src: str) -> list[EventImpact]:
    out: list[EventImpact] = []
    for m in _IMPACT.finditer(text):
        phrase, low, high = m.group(1), _money(m.group(2)), _money(m.group(3))
        if low is None or high is None:
            continue
        # direction: the nearest reduce/increase verb in the ~90 chars before the phrase. A bare
        # 'X by approximately $A to $B' with no directional verb is not an event impact — skipped.
        pre = text[max(0, m.start() - 90):m.start() + len(phrase)]
        dirs = list(_DIR_BACK.finditer(pre))
        if not dirs:
            continue
        d = dirs[-1].group(1).lower()
        direction = "increase" if d.startswith(("increas", "rais", "improv")) else "reduce"
        period_m = re.search(r"(20\d\d\s+annualized|annualized|20\d\d)", phrase, re.I)
        out.append(EventImpact(
            metric=_impact_metric(phrase), effect=direction, low=low, high=high,
            period=period_m.group(1).strip() if period_m else "",
            verbatim=_verbatim(text, m.start(), m.end()), source_ref=src,
        ))
    return out


# --- (PR-B A1) operating drivers — pricing actions + narrow leading indicators -------------------
# DEMOTED per the pre-sign-off diagnosis: pricing language is REAL (VITL) but KPI yield on this
# cohort is thin/noisy, so KPI is narrow (a shipped/added verb must GOVERN the number+unit — not
# adjacency) with the two observed false-positive shapes pinned out: an expense line-item carrying a
# unit word (FUBO), and a product spec ('290Ah cell', MVST). Pricing rows are QUALITATIVE by default
# (a headline '7% increase' is revenue growth, NOT a price change) — value_num is set ONLY when a %
# binds tightly to the price. M&A/merger boilerplate ('purchase price adjustment') is excluded.
_PRICING = re.compile(
    r"(strategic\s+pricing\s+actions?|pricing\s+actions?|list\s+price\s+increases?|"
    r"price\s+increases?|rais(?:e|ed|ing)\s+(?:our\s+|list\s+)?prices?|"
    r"increas(?:e|ed|ing)\s+(?:our\s+|the\s+)?(?:average\s+)?(?:selling\s+)?prices?)"
    # THE PHRASE MUST END AT A WORD BOUNDARY. Without it "price increases?" matched INSIDE "price
    # increased": Westlake's "average sales price increased 14%" — a realized market price in one
    # segment, beside another segment's 3% fall — became a bare "price increase" pricing-action row
    # that the synthesis is told to ground price points in.
    r"\b",
    re.I)
_PRICING_PCT = re.compile(  # a % TIGHTLY bound to the price action (else stays qualitative) — the
    # gap forbids COMMAS and DIGITS and is short, so a nearby UNRELATED % ('net of 8% rebates',
    # 'offset by 4% higher logistics', '…to gross margin of 40%') can't misbind as the price change.
    r"pric\w+[^.,\d]{0,24}?(?:of|by)\s+([\d.]+)\s?%"
    r"|([\d.]+)\s?%\s+(?:list\s+)?price\s+increase", re.I)
_MA_CONTEXT = re.compile(
    r"purchase\s+price\s+adjustment|merger\s+agreement|acquisition\s+agreement|indemnif\w+|"
    r"escrow", re.I)
_KPI_UNIT = (r"MWh|GWh|units|vehicles|members|subscribers|customers|locations|stores|procedures|"
             r"shipments|deliveries|tons")
# a shipped/added/etc. verb must GOVERN the number+unit (≤40 chars before) — adjacency alone is not
# a KPI (rejects 'Subscriber related expenses 946,705' and the '290Ah cell' product spec).
_KPI = re.compile(
    r"(shipped|delivered|added|produced|served|installed|sold|reached|grew\s+to|"
    r"increased\s+to)\s+(?:approximately\s+|about\s+|~)?([\d,][\d,.]*)\s+(" + _KPI_UNIT + r")\b",
    re.I)
_KPI_EXCLUDE = re.compile(r"expense|cost\s+of", re.I)


def operating_drivers(text: str, *, source_ref: str) -> list[OperatingDriver]:
    """(PR-B A1) Pricing-action + narrow leading-indicator rows from a 99.1 release. Pricing rows
    are verbatim-bound and QUALITATIVE unless a % binds tightly to the price; KPI rows require a
    governing shipped/added verb. M&A boilerplate and expense-line unit words are excluded. Empty is
    an honest miss the collector flags — the diagnosis expects thin KPI yield on this cohort."""
    out: list[OperatingDriver] = []
    seen: set[str] = set()
    for m in _PRICING.finditer(text):
        window = text[max(0, m.start() - 60):m.end() + 60]
        if _MA_CONTEXT.search(window):  # a merger/indemnity 'price' clause is not a pricing action
            continue
        if re.search(r"\b(?:not|no|without|never)\s+\w*$|n['’]t\s+\w*$",
                     text[max(0, m.start() - 18):m.start()], re.I):
            continue  # a NEGATED statement ('did not raise prices', 'no price increases') isn't one
        phrase = re.sub(r"\s+", " ", m.group(0)).strip().lower()
        if phrase in seen:
            continue
        seen.add(phrase)
        pm = _PRICING_PCT.search(text[m.start():m.end() + 60])
        pct = _money(pm.group(1) or pm.group(2)) if pm else None
        out.append(OperatingDriver(
            kind=DriverKind.PRICING_ACTION, metric="pricing action", period=_period_near(
                text, m.start(), m.end()) or None,
            value=(f"{phrase} — {pct:g}%" if pct is not None else phrase),
            value_num=pct, unit="%" if pct is not None else None,
            verbatim=_verbatim(text, m.start(), m.end(), cap=200), source_ref=source_ref,
            tier="anchored",
        ))
        if len(seen) >= 4:  # dedup-cap pricing phrases (a release repeats them) — no silent flood
            break
    for m in _KPI.finditer(text):
        pre = text[max(0, m.start() - 32):m.start()]
        if _KPI_EXCLUDE.search(pre):  # 'Subscriber related expenses 946,705' is NOT a volume KPI
            continue
        num = _money(m.group(2))
        if num is None:
            continue
        unit = m.group(3)
        key = f"{num}|{unit.lower()}"
        if key in seen:
            continue
        seen.add(key)
        out.append(OperatingDriver(
            kind=DriverKind.LEADING_INDICATOR, metric=f"{m.group(1).lower()} ({unit.lower()})",
            period=_period_near(text, m.start(), m.end()) or None,
            value=f"{m.group(2)} {unit}", value_num=num, unit=unit,
            verbatim=_verbatim(text, m.start(), m.end(), cap=200), source_ref=source_ref,
            tier="anchored",
        ))
    return out


def parse_release(text: str, *, source_ref: str) -> ReleaseExtract:
    """Parse ONE 99.1 exhibit's normalized text into a source-bound ReleaseExtract. Each empty
    section fails loud with a qa_flag — a miss is UNKNOWN, never a fabricated value."""
    guidance_notes: list[str] = []
    guidance = _guidance(text, source_ref, guidance_notes)
    reconciliation = _reconciliation(text, source_ref, _release_frame(text))
    one_offs = _one_offs(text, source_ref)
    event_impacts = _event_impacts(text, source_ref)
    flags: list[str] = list(guidance_notes)
    if not guidance and not guidance_notes:
        # ONLY when nothing was found at all. A release whose guidance was FOUND and refused states
        # guidance — saying "no anchored pattern matched" there would be the false-UNKNOWN shape.
        flags.append(f"no anchored pattern matched — guidance/outlook: {source_ref}")
    if not reconciliation:
        flags.append(f"no anchored pattern matched — non-GAAP reconciliation: {source_ref}")
    return ReleaseExtract(
        source_ref=source_ref, guidance=guidance, reconciliation=reconciliation,
        one_offs=one_offs, event_impacts=event_impacts, qa_flags=flags,
    )
