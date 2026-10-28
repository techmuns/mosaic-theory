"""How many ordinary shares one depositary share represents — read from the issuer's own filing.

A DEPOSITARY LINE IS PRICED PER ADS, AND ITS ISSUER REPORTS PER ORDINARY SHARE. QFIN trades at
$5.67 an ADS and reports diluted EPS of CNY 22.01 per ordinary share, and each ADS is two ordinary
shares; set side by side without the ratio, every per-share figure is off by that factor (TSM 5,
IPX 10, KT 0.5). The universe already sizes a depositary line on Polygon's ADS-denominated count
(#541) and needs no ratio; what needs it is every PER-SHARE figure set against the ADS price: a
P/E level, a value per share, a share count a price is multiplied by. STATE §5.0 row 4, FPI4.

WHERE THE RATIO IS STATED (this reader over the 85 depositary-typed lines of the 2026-10-16 primary
population, each line's latest periodic report filed on or before 2026-10-16; measured
2026-10-28):
- **a 12(b) title on the cover** — "American depositary shares, each representing two Class A
  ordinary shares" (QFIN): 59. EVERY depositary title on the cover is read, not only the row a
  symbol match keeps: HSBC tags its symbol to its ordinary-share row as well as its ADS row, and
  the match keeps the ordinary one, which states no ratio. TSM and ASML register only shares.
- **otherwise the filing's text** — "each ADS represents five (5) common shares" (TSM): 18.
- **refused, 8**: BMA and GGB state none; GRFS and HIMX state two ratios (a change and its
  successor); BSBR, KOF, TV and VLRS count UNITS or CPOs, not shares.

EXACTLY ONE VALUE, OR A REFUSAL WITH ITS REASON. A filing that states two ratios (BIDU's 20-F
carries its current eight-shares ADS beside the ten-ADS-per-share it replaced) cannot say which is
current from the words alone, and guessing one is the silent 1:1 assumption with a different
number. The titles are preferred to the text because they are the issuer's structured statement of
what it registered; the text is read only when no title states a ratio.

A FRACTION IS A FRACTION. "each representing one-half of one share" (KT) is 0.5 and "3/5 of one
share" (SMFG) is 0.6 — the first cut of the measurement read them as 1 and 3, because a count
pattern matched the numerator. Every count pattern now refuses a number followed by a fraction.
"""

from __future__ import annotations

import html as htmllib
import re
from datetime import date
from typing import Any, Literal, NamedTuple

from vinci.resolver.instrument import cover_lines
from vinci.schemas.listing import AdsRatio

#: a 12(b) title (or a sentence) that is about depositary shares at all
DEPOSITARY_WORDS = re.compile(r"depositary|depository|\bADSs?\b|\bADRs?\b", re.I)

_COUNT_WORDS: dict[str, float] = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
    "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
    "twenty-five": 25, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "eighty": 80,
    "one hundred": 100, "hundred": 100, "two hundred": 200, "four hundred": 400,
}
_FRACTION_WORDS: dict[str, float] = {
    "half": 2, "halves": 2, "third": 3, "quarter": 4, "fourth": 4, "fifth": 5, "sixth": 6,
    "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10, "twentieth": 20, "fortieth": 40,
    "fiftieth": 50, "hundredth": 100,
}
_FRAC_ALT = (r"halves|half|thirds?|quarters?|fourths?|fifths?|sixths?|sevenths?|eighths?|"
             r"ninths?|tenths?|twentieths?|fortieths?|fiftieths?|hundredths?")
_NUM = (r"(\d+(?:\.\d+)?|"
        + "|".join(sorted(map(re.escape, _COUNT_WORDS), key=len, reverse=True)) + r")")
#: a number followed by a fraction word or "/n" is a NUMERATOR, never a count (KT, SMFG)
_NOT_A_NUMERATOR = r"(?![\s-]*(?:/|" + _FRAC_ALT + r"))\b"
_RIGHT_TO = r"(?:the\s+right\s+to\s+receive\s+)?"
#: "depository" is how EC and IX spell it on their own covers
_ADS_NOUN = (r"(?:ADSs?|ADRs?|American\s+deposit(?:a|o)ry\s+(?:shares?|receipts?)|"
             r"(?:global|GDSs?)\s+deposit(?:a|o)ry\s+shares?)")
#: an aside between the noun and its ratio: '(the “ADSs”)', '(as evidenced by American Depositary
#: Receipts)' (EC, IX, ITUB)
_ASIDE = r"(?:\s*\([^()]{0,90}\))?"
#: "one-half of one share" (KT), "five-ninths of one share" (SKM): numerator, then denominator
_FRACTION = (r"(?:(" + "|".join(sorted(map(re.escape, _COUNT_WORDS), key=len, reverse=True))
             + r"|a)[\s-]+)?(" + _FRAC_ALT + r")\s+of\s+(?:one|an?)\b")
_SLASH = r"(\d+)\s*/\s*(\d+)(?:th|st|nd|rd)?\s+of\s+(?:one|an?)\b"
_REPRESENT = r"represent(?:s|ing)?\s+" + _RIGHT_TO

#: ordinary shares per ADS = the captured count. Each needs the ADS NOUN beside the verb, because
#: a filing's text says "represents" about many other things.
_PER_ADS = [
    # "each ADS represents five (5) common shares" (TSM), "each ADR represents two Eni shares" (E)
    re.compile(r"each\s+" + _ADS_NOUN + r"\s+" + _REPRESENT + _NUM + _NOT_A_NUMERATOR, re.I),
    # "American depositary shares, each representing two Class A ordinary shares" (QFIN), with an
    # aside or a bracket before "each" (IX, ERIC)
    re.compile(_ADS_NOUN + _ASIDE + r"\s*,?\s*\(?\s*each\s+(?:of\s+which\s+)?" + _REPRESENT
               + _NUM + _NOT_A_NUMERATOR, re.I),
    # "one ADS represents two ordinary shares" (ASX)
    re.compile(r"\bone\s+" + _ADS_NOUN + r"\s+" + _REPRESENT + _NUM + _NOT_A_NUMERATOR, re.I),
    # "a ratio of one ADS to ten ordinary shares"
    re.compile(r"ratio\s+of\s+(?:one|1)\s+ADS\s+(?:to|for)\s+" + _NUM + _NOT_A_NUMERATOR, re.I),
]
#: "every three ADSs represent two Class A ordinary shares" (RERE): M / N
_N_ADS_REPRESENT_M = re.compile(r"(?:every\s+)?" + _NUM + r"\s+" + _ADS_NOUN + r"\s+" + _REPRESENT
                                + _NUM + _NOT_A_NUMERATOR, re.I)
#: "each representing one-half of one share" (KT), "representing 3/5 of one share" (SMFG)
_FRACTION_PATTERNS = [
    re.compile(_ADS_NOUN + r"[^.]{0,60}?" + _REPRESENT + _FRACTION, re.I),
    re.compile(_ADS_NOUN + r"[^.]{0,60}?" + _REPRESENT + _SLASH, re.I),
]
#: "American Depositary Shares, each three representing one Class A common share" (TAL): three
#: ADSs per share
_EACH_N_REPRESENTING_M = re.compile(r"each\s+" + _NUM + r"\s+" + _REPRESENT + _NUM
                                    + _NOT_A_NUMERATOR, re.I)
#: AN ADS OF UNITS IS NOT AN ADS OF SHARES. "each representing five Ordinary Participation
#: Certificates" (TV), "ten CPOs" (CX), "10 BD Units" (FMX), "10 units" (KOF): each unit is itself a
#: bundle of shares, and how many is not in these words — so the count is refused, never read as
#: shares.
_UNIT_NOUN = re.compile(r"^\W*(?:\(\d+\)\s*)?(?:[\w’'-]+\s+){0,2}?(?:units?\b|CPOs?\b|"
                        r"(?:ordinary\s+)?participation\s+certificates?)", re.I)
#: INSIDE A DEPOSITARY 12(b) TITLE the noun is given — the title is ABOUT the ADS — so any
#: "representing N" counts: "American Depositary Share representing 100 Series B Shares" (TLK)
_TITLE_COUNT = re.compile(_REPRESENT + _NUM + _NOT_A_NUMERATOR, re.I)
_TITLE_FRACTIONS = [re.compile(_REPRESENT + _FRACTION, re.I), re.compile(_REPRESENT + _SLASH, re.I)]
#: a quote is cut to this many characters either side of the match, and SAYS it was cut
_QUOTE_PAD = 80


def _count(word: str) -> float | None:
    w = " ".join(word.lower().split())
    if re.fullmatch(r"\d+(?:\.\d+)?", w):
        return float(w)
    return _COUNT_WORDS.get(w)


def _quote(text: str, start: int, end: int) -> str:
    lo, hi = max(0, start - _QUOTE_PAD), min(len(text), end + _QUOTE_PAD)
    return ("…" if lo else "") + text[lo:hi].strip() + ("…" if hi < len(text) else "")


class Statements(NamedTuple):
    """What a piece of text states: each ratio with its quote, in text order, and each ADS it
    describes as a bundle of UNITS rather than of shares (quoted, never counted)."""

    ratios: list[tuple[float, str]]
    units: list[str]


def _collect(text: str, rules: list[tuple[re.Pattern[str], str]]) -> Statements:
    """Every statement the rules find, in text order. A span one rule has read is never re-read by
    a later one — one statement is one statement — so the SPECIFIC rules run before the general
    count: in a title, "every three ADSs represent two" must be read as N-for-M before "represent
    two" can be read as two (RERE). What keeps "one-half" from being read as one is not the order
    but `_NOT_A_NUMERATOR`, which every count pattern carries."""
    found: list[tuple[int, float, str]] = []
    taken: list[tuple[int, int]] = []
    units: list[str] = []
    for pattern, kind in rules:
        for m in pattern.finditer(text):
            if any(m.start() < hi and lo < m.end() for lo, hi in taken):
                continue
            if _UNIT_NOUN.match(text[m.end():m.end() + 60]):
                taken.append((m.start(), m.end()))
                units.append(_quote(text, m.start(), m.end()))
                continue
            if kind == "fraction":
                num = _count(m.group(1)) if m.group(1) and m.group(1).lower() != "a" else 1.0
                word = m.group(2).lower()
                den = _FRACTION_WORDS.get(word) or _FRACTION_WORDS.get(word.removesuffix("s"))
                v: float | None = num / den if num and den else None
            elif kind == "slash":
                v = int(m.group(1)) / int(m.group(2)) if int(m.group(2)) else None
            elif kind == "n_for_m":   # N ADSs represent M shares
                n, mm = _count(m.group(1)), _count(m.group(2))
                v = mm / n if n and mm else None
            else:
                v = _count(m.group(1))
            if v is None or v <= 0:
                continue
            taken.append((m.start(), m.end()))
            found.append((m.start(), v, _quote(text, m.start(), m.end())))
    return Statements([(v, q) for _pos, v, q in sorted(found)], units)


def statements(text: str) -> Statements:
    """Everything a filing's TEXT states. Never deduplicated: the caller decides what several
    statements mean."""
    return _collect(text, [(_FRACTION_PATTERNS[0], "fraction"), (_FRACTION_PATTERNS[1], "slash"),
                           (_N_ADS_REPRESENT_M, "n_for_m"),
                           *((p, "count") for p in _PER_ADS)])


def title_statements(title: str) -> Statements:
    """The same, for one depositary 12(b) title, where the ADS noun is given by the title itself."""
    t = " ".join(title.split())
    return _collect(t, [(_TITLE_FRACTIONS[0], "fraction"), (_TITLE_FRACTIONS[1], "slash"),
                        (_N_ADS_REPRESENT_M, "n_for_m"), (_EACH_N_REPRESENTING_M, "n_for_m"),
                        (_TITLE_COUNT, "count")])


def flatten(doc_html: str) -> str:
    """The document's words with tags, entities and runs of whitespace (nbsp included) folded —
    enough for an anchored sentence pattern. Not ``graph.filings.html_to_text``: that one imports
    the EDGAR client, which this low-level resolver module must not."""
    t = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", doc_html)
    return " ".join(htmllib.unescape(re.sub(r"<[^>]+>", " ", t)).split())


def _decide(got: Statements, source: Literal["12(b) title", "filing text"],
            where: dict[str, Any]) -> AdsRatio | None:
    """Exactly one ratio, or a refusal saying why — None when this source states nothing."""
    if got.units:
        return AdsRatio(status="refused", reason=(
            f"the {source} describes the ADS as a bundle of UNITS, not ordinary shares, and does "
            f"not say how many shares a unit holds: “{got.units[0]}”"), **where)
    if not got.ratios:
        return None
    values = sorted({round(v, 6) for v, _q in got.ratios})
    if len(values) == 1:
        # the filing's own value, not its 6-place rounding (2/3, not 0.666667); the rounding only
        # decides whether several statements agree
        return AdsRatio(status="known", ordinary_per_ads=got.ratios[0][0], source=source,
                        quote=got.ratios[0][1], **where)
    listed = ", ".join(f"{v:g}" for v in values)
    if source == "12(b) title":
        why = f"the cover's depositary 12(b) titles state {len(values)} different ratios ({listed})"
    else:
        why = (f"no 12(b) title states a ratio and the filing's text states {len(values)} "
               f"different ones ({listed}): a ratio change it describes cannot be told from the "
               f"current ratio by its words alone")
    return AdsRatio(status="refused", reason=f"{why} — ordinary shares per ADS", **where)


def read_ratio(doc_html: str, *, form: str, filed: date, accession: str) -> AdsRatio:
    """The ratio a periodic filing states: from its depositary 12(b) titles, else its text."""
    return ratio_from(cover_lines(doc_html), flatten(doc_html),
                      form=form, filed=filed, accession=accession)


def ratio_from(lines: list[tuple[str | None, str | None]], text: str, *, form: str, filed: date,
               accession: str) -> AdsRatio:
    """:func:`read_ratio` on a cover's (symbol, 12(b) title) lines and the filing's flattened text —
    every depositary title first, the text only when no title states a ratio."""
    where: dict[str, Any] = {"form": form, "filed": filed, "accession": accession}
    joined = Statements([], [])
    for _sym, t in lines:
        if t and DEPOSITARY_WORDS.search(t):
            st = title_statements(t)
            joined.ratios.extend(st.ratios)
            joined.units.extend(st.units)
    decided = _decide(joined, "12(b) title", where)
    if decided is None:
        decided = _decide(statements(text), "filing text", where)
    return decided or AdsRatio(status="refused", reason=(
        "neither a depositary 12(b) title on the cover nor the filing's text states how many "
        "ordinary shares an ADS represents"), **where)
