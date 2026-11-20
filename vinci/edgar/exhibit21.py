"""Exhibit 21 — the subsidiaries list a 10-K files — read as source-bound names (W86, $0).

WHAT IT IS FOR. CIQ Key Developments files other companies' developments under a filer (W85): a
Lyft row under Alphabet, a Kartoon Studios row under Amazon. Telling the filer's OWN units (Google,
Whole Foods, Shipt) from the companies it merely invests in or partners with needs a list the filer
itself states. Regulation S-K Item 601(b)(21) makes every 10-K file one, as an exhibit typed
``EX-21`` (or ``EX-21.1``, ``EX-21.01``). This module reads it. It does not attribute anything.

WHAT THE LIST CANNOT SAY. Item 601(b)(21)(ii) lets a filer omit every subsidiary that, taken
together, would not be a significant subsidiary, and most large filers do. Amazon's list names nine
companies and Whole Foods is not one of them. So a name ON the list is the filer's own statement
that the name is a subsidiary, or for some filers an affiliate. A name NOT on the list is not
evidence that it is not the filer's own, whether or not the exhibit says it omits the rest: Uber's
2025 list names 13 companies and states no omission. :attr:`Exhibit21Read.states_omission` carries
the exhibit's own statement when it makes one, and :attr:`Exhibit21Read.names_affiliates` flags a
list that names affiliates too (Lilly's "Subsidiaries & Affiliates"). A reader that treats "not
listed" as "not own" selects on DISCLOSURE FORM (CLAUDE.md).

HOW IT READS.
- The filing is the filer's newest original ``10-K`` filed by ``through``. An amendment is not
  read: a 10-K/A rarely refiles the exhibit, and Part III amendments never do.
- The exhibit is found by the TYPE EDGAR's own SGML header gives each document, never by its
  filename (the lesson of :func:`vinci.edgar.release_parse.exhibit_991_urls`). An unreadable header
  is ``unread``, never ``no_ex21``: absence is asserted only off a header that was read.
- A table exhibit gives one name per row, taken from the row's first non-empty cell, and the next
  non-empty cell as its jurisdiction. A row whose first cell is column vocabulary ("Name of
  Subsidiary", "Jurisdiction") with no corporate suffix is the header and is skipped.
- An exhibit with no table gives one name per text line that ends in a corporate form ("Inc.",
  "LLC", "s.r.o." …), once a trailing "(MN)" or "- Delaware" is set aside as its jurisdiction
  ("Target Brands, Inc. (MN)"). A note after the form ("dba …", "… Branch", "i.L.") does not hide
  it. The exhibit's own heading ("Subsidiaries of … Company") is never a name, in either mode. A
  name with no form text mode can see ("Visa International Service Association", "Concentrix
  Maroc") is not read in text mode: of the 1,105 names the 26 page filers' tables list (EDGAR read
  2026-11-20), 62 are such names, 49 of them Concentrix's. Only TGT's exhibit has no table.
- The registrant's own name is never a subsidiary of itself, and is dropped from the list. It is
  carried beside it (:attr:`Exhibit21Read.registrant`), and an entity that IS the registrant
  matches at its own tier, ``registrant``.
- An exhibit read with no name found is ``no_names``: a parse failure, reported, never an empty
  list.

MATCHING (:func:`match_entity`) reports three tiers, each separately, so a consumer chooses one
knowingly:
- ``registrant``: the entity is the filer itself, normalised ("Alphabet" = "Alphabet Inc.");
- ``exact``: the entity as given equals a listed name, whitespace collapsed;
- ``normalised``: equal once case, punctuation and trailing corporate suffixes are set aside
  ("Google" = "Google LLC");
- ``word_prefix``: the normalised entity is the leading whole words of a listed name ("Whole Foods"
  in "Whole Foods Market, Inc."; "LillyDirect" in "LillyDirect Pharmacy, LLC"). It is looser, and
  it is reported as its own tier, never folded into the other two.

WHICH TIERS CONFIRM OWN (:attr:`EntityMatch.confirms_own`): ``exact`` and ``normalised`` on a list
that names no affiliates, for a row that states no share of 50% or less, and ``registrant``.
``word_prefix`` is a lead only: "NBC" leads 28 of TJX's names and "Global" a Concentrix trustee.
A bare filer name ("Uber", "Amazon") lands on one subsidiary's row ("Uber B.V.", "Amazon.com
Services LLC"): it is the filer's own, and the row it names is one of several. No tier refutes.

Every listed name carries its ``source_ref``: the form, the accession, the exhibit's own type and
its URL.
"""

from __future__ import annotations

import bisect
import html
import re
import unicodedata
from datetime import date, timedelta
from typing import Literal, NamedTuple

from bs4 import BeautifulSoup
from pydantic import BaseModel

from vinci.edgar.client import EdgarClient
from vinci.edgar.submissions import RegistrantHistory
from vinci.netcache import CachedHttp, HttpError
from vinci.resolver.index import pad_cik

_ARCHIVE = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{doc}"
_HEADERS = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{acc_dashed}-index-headers.html"
#: EDGAR's per-document SGML header (served HTML-escaped inside the -index-headers page).
_SGML_DOC = re.compile(r"<TYPE>([^\s<]+)[\s\S]{0,400}?<FILENAME>([^\s<]+)", re.I)
#: ``EX-21``, ``EX-21.1``, ``EX-21.01`` — never EX-210 or an EX-2.1 that happens to follow.
_EX21_TYPE = re.compile(r"EX-21(?:\.\d+)?", re.I)
_TEXT_DOC = (".htm", ".html", ".txt")

#: Trailing corporate-form words, as normalised tokens. A tuple is one multi-token form ("l l c"
#: is "L.L.C." with its punctuation set aside). "Holdings", "Group" and "International" are NOT
#: forms: they tell two subsidiaries apart ("XXVI Holdings Inc." is not "XXVI Inc.").
_SUFFIXES: tuple[tuple[str, ...], ...] = tuple(sorted({
    ("inc",), ("incorporated",), ("llc",), ("l", "l", "c"), ("lc",), ("pllc",), ("llp",),
    ("l", "l", "p"), ("lp",), ("l", "p"), ("ltd",), ("limited",), ("corp",), ("corporation",),
    ("co",), ("company",), ("plc",), ("p", "l", "c"), ("ulc",), ("gmbh",), ("ag",), ("kg",),
    ("sa",), ("s", "a"), ("sas",), ("s", "a", "s"), ("sarl",), ("s", "a", "r", "l"), ("s", "à",
    "r", "l"), ("srl",), ("s", "r", "l"), ("spa",), ("s", "p", "a"), ("bv",), ("b", "v"), ("nv",),
    ("n", "v"), ("pty",), ("pte",), ("kk",), ("ab",), ("as",), ("a", "s"), ("oy",), ("sl",),
    ("s", "l"), ("sa", "de", "cv"), ("s", "a", "de", "c", "v"), ("de", "cv"), ("de", "c", "v"),
    ("s", "de", "rl", "de", "cv"), ("s", "de", "r", "l", "de", "c", "v"), ("ltda",), ("lda",),
    ("sp", "z", "o", "o"), ("pvt",), ("private",), ("bhd",), ("sdn",), ("ehf",), ("aps",),
    # forms a corpus survey found missing (review round 2 of #1152: 182 of 1,105 listed names
    # ended in a form this table lacked, so a text exhibit dropped them)
    ("s", "p", "z", "o", "o"), ("s", "r", "o"), ("d", "o", "o"), ("dooel",), ("s", "a", "c"),
    ("s", "a", "e"), ("s", "l", "u"), ("slu",), ("s", "a", "u"), ("k", "k"), ("g", "k"), ("kft",),
    ("eood",), ("ood",), ("shpk",), ("wll",), ("c", "v"), ("cv",),
    ("limited", "partnership"), ("şirketi",), ("sirketi",), ("sia",), ("uab",), ("oü",), ("ou",),
    ("fzco",), ("fze",), ("fz", "llc"), ("a", "e"), ("p", "c"), ("sasu",), ("limitada",),
    ("ges", "m", "b", "h"), ("s", "a", "c", "i"), ("s", "a", "l"), ("s", "c"), ("şti",), ("sti",),
    ("fllc",),
}, key=len, reverse=True))

#: Words that mark a line as a company in a text exhibit and are NOT set aside when names are
#: compared: "NBC Trust" is a company, and not the same one as an "NBC".
_FORM_MARKS: tuple[tuple[str, ...], ...] = (("trust",),)
#: Forms some jurisdictions put FIRST ("PT Concentrix Services Indonesia", "UAB Eli Lilly
#: Lietuva", "LLC IT-PARK UNIVERSITY"): a text line that opens with one is a company.
_LEADING_FORMS = frozenset({"pt", "uab", "llc", "llp", "spa", "ooo", "ao", "tov", "sia", "oy"})

#: A header cell's vocabulary: a column title ("Name of Subsidiary", "Entity", "Jurisdiction") or a
#: section title ("Operating Subsidiaries", TJX's), never a company.
_HEADER_CELL = re.compile(
    r"^(?:(?:legal|company|entity|exact)\s+)?names?\b|^subsidiar(?:y|ies)\b|^entit(?:y|ies)\b"
    r"|\bsubsidiar(?:y|ies)$|jurisdiction|incorporat|\borgani[sz]ation\b|^state\b|^country\b"
    r"|percent|owner|^%", re.I)
#: The exhibit's own heading ("Subsidiaries of The Simply Good Foods Company", "List of Significant
#: Subsidiaries of Visa Inc."): never a subsidiary, though it may end in a corporate form.
_HEADING = re.compile(r"^(?:exhibit\s+[\d.]+\W*)?(?:list\s+of\s+)?(?:(?:significant|principal)\s+)?"
                      r"subsidiar(?:y|ies)\b", re.I)
#: A note after a listed name's form that is not part of the form: a trade name ("…, Inc., dba
#: Werner Fleet Sales"), a branch ("… Ltd ROHQ", "… - Philippine Branch"), or a liquidation
#: ("Emakina.DE GmbH i.L."). Set aside only to find the form; the name is kept as listed.
_TAIL_NOTE = re.compile(r"(?:,?\s+(?:dba|d/b/a)\b.*"
                        r"|\s*[-–—(]?\s*(?:[\w'’.,-]+\s+){0,3}\(?branch\b.*"
                        r"|\s+(?:[-–—]\s+)?(?:sucursal|sucrsal|succursale)\b.*|\s+rohq\b.*|\s+.*\bşubesi"
                        r"|\s+i\.\s?l\.?|\s+in\s+liquidation)$", re.I)
#: EDGAR's conformed-name tags ("TJX COMPANIES INC /DE/", "… /NEW/"): never part of the name.
_STATE_TAG = re.compile(r"(?:\s*/[^/\s]{1,8}/)+\s*$")
#: A cell that only numbers its row ("1.", Werner's; "(a)"): skipped when looking for the name.
_ENUM_CELL = re.compile(r"\(?\d{1,4}[.)]?|\(?(?:[a-z]|[ivx]+)[.)]", re.I)
#: A stated ownership share in a row ("100 %", "(40.0% interest)"). A share below 100 says the
#: listed company is not wholly owned, and a minority share says it is no subsidiary at all.
_PERCENT = re.compile(r"(\d{1,3}(?:\.\d+)?)\s*%")
#: The exhibit's statement that it omits the rest (Item 601(b)(21)(ii)), however worded: the rule's
#: citation, "omit" beside "significant", or "not significant".
_OMISSION = re.compile(
    r"601\s*\(b\)\s*\(21\)\s*\(ii\)|\bomit(?:s|ted|ting)?\b.{0,200}?\bsignificant\b"
    r"|\bsignificant\b.{0,200}?\bomit(?:s|ted|ting)?\b|\bnot\s+(?:be\s+)?significant\b", re.I)
#: A heading that names the list as significant subsidiaries only ("LIST OF SIGNIFICANT
#: SUBSIDIARIES", Amazon's whole statement of it), used when no sentence states the omission.
_SIGNIFICANT_HEADING = re.compile(r"\bsignificant\s+subsidiar(?:y|ies)\b", re.I)
#: A sentence boundary that is not a company form's own full stop ("Alphabet Inc., omitting").
_SENTENCE_END = re.compile(
    r"(?<!\bInc\.)(?<!\bCo\.)(?<!\bLtd\.)(?<!\bCorp\.)(?<!\bL\.P\.)(?<!\bN\.V\.)(?<!\bS\.A\.)"
    r"(?<=[.:;])\s+(?=[A-Z(])")
#: The longest statement kept, cut on a word.
_MAX_STATEMENT = 400
_AFFILIATES = re.compile(r"\baffiliat(?:e|es|ed)\b", re.I)
#: A text line longer than this is prose, not one company's name.
_MAX_NAME_LINE = 160
_TRAILING_PAREN = re.compile(r"\s*\(([^()]*)\)\s*$")
#: How far back of ``through`` the 10-Ks are read: a year and a half, so a late filer's newest 10-K
#: by that day is inside the window.
_TENK_LOOKBACK_DAYS = 550


Status = Literal["listed", "no_ex21", "no_names", "unread", "no_10k"]
Tier = Literal["registrant", "exact", "normalised", "word_prefix", "not_listed", "no_ex21",
               "no_names", "unread",
               "no_10k"]


class Subsidiary(BaseModel, frozen=True):
    """One company an Exhibit 21 lists, as the filer wrote it."""

    name: str
    jurisdiction: str | None
    #: The ownership share the row states, in percent, or None when it states none (most rows).
    #: Parsed from the row's own cells; Par Pacific lists "Yellowstone Pipe Line Company (40.0%
    #: interest)", an investee by any reading, on its subsidiaries list.
    stated_percent: float | None = None
    source_ref: str  # "10-K <accession> <exhibit type> · <url>"


class Exhibit21Read(BaseModel, frozen=True):
    """What one filer's newest 10-K files as Exhibit 21, or why nothing was read."""

    cik: str
    status: Status
    #: The filer's registrant name in force at the read's ``through`` (today's when None), from
    #: EDGAR's submissions document; None when it states none.
    registrant: str | None = None
    #: The registrant's name when the 10-K was filed (its list is written under it), or None.
    filed_as: str | None = None
    accession: str | None = None
    filing_date: date | None = None
    exhibit_urls: tuple[str, ...] = ()
    names: tuple[Subsidiary, ...] = ()
    #: The exhibit's statement that it omits insignificant subsidiaries, verbatim, or None. When
    #: set, a name NOT on the list is not evidence that it is not the filer's own. None is NOT a
    #: statement that the list is complete: Uber's 2025 list names 13 companies and says nothing.
    states_omission: str | None = None
    #: True when the exhibit's own text says it lists affiliates as well as subsidiaries, so a
    #: listed name may be an affiliate rather than a subsidiary.
    names_affiliates: bool = False
    note: str = ""


class EntityMatch(BaseModel, frozen=True):
    """Whether an entity is on a filer's Exhibit 21, and at which tier."""

    entity: str
    tier: Tier
    listed: Subsidiary | None = None
    #: Copied from the read: the exhibit says it omits insignificant subsidiaries. ``not_listed`` is
    #: never evidence that the entity is not the filer's own, and here the filer says so itself.
    list_states_omission: bool = False
    #: Whether this match is the filer's own statement that the entity is its own: ``exact`` or
    #: ``normalised`` on a list that names no affiliates and states no share of 50% or less, or
    #: ``registrant``. ``word_prefix`` never confirms ("NBC" leads 28 of TJX's names, "Global" a
    #: Concentrix trustee); ``not_listed`` never refutes. The one-sided rule, as a value.
    confirms_own: bool = False


# --- normalisation ------------------------------------------------------------------------------

def _collapse(s: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", s).split())


def _tokens(name: str) -> list[str]:
    """The name's words, casefolded, punctuation set aside, a trailing parenthetical dropped."""
    s = _STATE_TAG.sub("", unicodedata.normalize("NFKC", name)).casefold()
    s = _TRAILING_PAREN.sub("", s)
    s = s.replace("&", " and ")
    s = re.sub(r"[^\w\s]|_", " ", s)
    toks = s.split()
    if len(toks) > 1 and toks[0] == "the":
        toks = toks[1:]
    return toks


def _strip_suffixes(toks: list[str]) -> list[str]:
    """``toks`` without its trailing corporate forms ("google llc" → "google"), never emptied."""
    changed = True
    while changed:
        changed = False
        for suf in _SUFFIXES:
            n = len(suf)
            if len(toks) > n and tuple(toks[-n:]) == suf:
                toks = toks[:-n]
                changed = True
                break
        if len(toks) > 1 and toks[-1] == "and":  # "Eli Lilly and Company" → "eli lilly"
            toks = toks[:-1]
            changed = True
    return toks


def normalise_name(name: str) -> str:
    """The comparison key of a company name: case, punctuation, a leading "The", a trailing
    parenthetical and trailing corporate forms set aside. "Amazon.com Services LLC" → "amazon com
    services"; "Google LLC" → "google"."""
    return " ".join(_strip_suffixes(_tokens(name)))


#: A corporate form's abbreviation and its spelt-out word, so the registrant's EDGAR name ("TARGET
#: CORP") and its own heading line ("Target Corporation") read as one name.
_FORM_WORDS = {"corp": "corporation", "inc": "incorporated", "co": "company", "ltd": "limited"}


def _full_key(name: str) -> str:
    """A name with its corporate form KEPT, spelt out: "Gartner, LLC" and "Gartner, Inc." differ,
    "TARGET CORP" and "Target Corporation" do not. The registrant is dropped from its own list only
    on this key: the normalised key would also drop every subsidiary that shares its base name."""
    s = _STATE_TAG.sub("", unicodedata.normalize("NFKC", name)).casefold().replace("&", " and ")
    toks = re.sub(r"[^\w\s]|_", " ", s).split()
    return " ".join(_FORM_WORDS.get(t, t) for t in toks)


def _form_at_end(name: str) -> bool:
    toks = _tokens(name)
    if len(toks) > 1 and toks[0] in _LEADING_FORMS:
        return True
    return any(len(toks) > len(s) and tuple(toks[-len(s):]) == s
               for s in (*_SUFFIXES, *_FORM_MARKS))


def _ends_in_suffix(name: str) -> bool:
    """Whether ``name`` ends in a corporate form, or in one followed by a note
    (:data:`_TAIL_NOTE`). Each place a note could start is tried, so a note never swallows the
    form before it ("… Group Inc. Costa Rica Branch")."""
    if _form_at_end(name):
        return True
    return any(_TAIL_NOTE.fullmatch(name[m.start():]) and _form_at_end(name[:m.start()])
               for m in re.finditer(r"[\s,(]", name) if m.start() > 0)


# --- the exhibit ---------------------------------------------------------------------------------

def _is_ex21_type(ty: str) -> bool:
    """An SGML document TYPE that is an Exhibit 21, whole: never EX-210 or EX-21A."""
    return _EX21_TYPE.fullmatch(ty.strip()) is not None


def ex21_documents(http: CachedHttp, cik: str, accession: str) -> list[tuple[str, str]] | None:
    """``(type, url)`` for every document EDGAR's SGML header types as Exhibit 21 in a filing.

    None when the header cannot be read or is not the expected shape: absence is asserted only
    from a header that was read. ``[]`` means it was read and the filing files no Exhibit 21."""
    acc = accession.replace("-", "")
    url = _HEADERS.format(cik=int(pad_cik(cik)), acc=acc, acc_dashed=accession)
    try:
        raw = http.get_text(url, ttl_seconds=None)
    except (HttpError, ValueError):
        return None
    text = html.unescape(raw)
    if "<TYPE>" not in text.upper():
        return None
    return [(ty.upper(), _ARCHIVE.format(cik=int(pad_cik(cik)), acc=acc, doc=fn))
            for ty, fn in _SGML_DOC.findall(text)
            if _is_ex21_type(ty) and fn.lower().endswith(_TEXT_DOC)]


class ListedRow(NamedTuple):
    """One row of an Exhibit 21 as parsed, before it is bound to its filing."""

    name: str
    jurisdiction: str | None
    stated_percent: float | None


def _split_jurisdiction(line: str) -> tuple[str, str | None]:
    """A text line's name and jurisdiction: a trailing "(MN)" or "- Delaware" is the jurisdiction
    when what precedes it ends in a corporate form. A parenthetical that states a share ("(40.0%
    interest)") stays in the name, as a table row keeps it."""
    m = _TRAILING_PAREN.search(line)
    if m and m.start() > 0 and _PERCENT.search(m.group(1)) is None:
        return line[:m.start()].strip(), (m.group(1).strip() or None)
    dash = re.match(r"^(.*\S)\s+[-–—]\s+([^-–—]+)$", line)
    if dash and _ends_in_suffix(dash.group(1)):
        return dash.group(1).strip(), dash.group(2).strip()
    return line.strip(), None


def _percent(text: str) -> float | None:
    m = _PERCENT.search(text)
    if m is None:
        return None
    v = float(m.group(1))
    return v if 0 < v <= 100 else None


def _table_rows(soup: BeautifulSoup) -> list[ListedRow]:
    out: list[ListedRow] = []
    for tr in soup.find_all("tr"):
        cells = [_collapse(c.get_text(" ", strip=True)) for c in tr.find_all(["td", "th"])]
        filled = [c for c in cells if c]
        while filled and _ENUM_CELL.fullmatch(filled[0]):
            filled = filled[1:]  # a row number, not the name
        if not filled:
            continue
        name = filled[0]
        if _HEADING.match(name) or (_HEADER_CELL.search(name) and not _ends_in_suffix(name)):
            continue  # the exhibit's heading, or a column or section title
        if len(name) > _MAX_NAME_LINE:
            continue
        rest = filled[1:]
        juris = next((c for c in rest if _PERCENT.fullmatch(c) is None and c != "%"), None)
        out.append(ListedRow(name, juris, _percent(" ".join(filled))))
    return out


def _text_rows(lines: list[str]) -> list[ListedRow]:
    out: list[ListedRow] = []
    for line in lines:
        line = _collapse(line)
        if not line or len(line) > _MAX_NAME_LINE:
            continue
        name, juris = _split_jurisdiction(line)
        if name and not _HEADING.match(name) and _ends_in_suffix(name):
            out.append(ListedRow(name, juris, _percent(line)))
    return out


def parse_exhibit21(doc: str, *, registrant: str | None = None,
                    filed_as: str | None = None) -> tuple[list[ListedRow], str]:
    """``(rows, prose)`` of one Exhibit 21 document: each listed row in the exhibit's order, and the
    exhibit's text outside its tables, one line per text block (where it states what it omits).

    The registrant's own name is dropped (:func:`_full_key`), under either of its names: the one in
    force at the read's cut and the one the 10-K was filed under. A row repeated verbatim (the same
    name and jurisdiction) is kept once; two rows that differ only in corporate form or
    jurisdiction are two companies and are both kept ("EPAM Systems LLC" in four countries)."""
    is_html = re.search(r"<\s*(?:html|body|table|tr|p|div|br)\b", doc, re.I) is not None
    if is_html:
        soup = BeautifulSoup(doc, "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()
        rows = _table_rows(soup)
        for t in soup(["table"]):
            t.decompose()
        lines = soup.get_text("\n", strip=True).splitlines()
        if not rows:
            rows = _text_rows(lines)
    else:
        lines = doc.splitlines()
        rows = _text_rows(lines)
    prose = "\n".join(c for c in (_collapse(x) for x in lines) if c)
    own = {_full_key(n) for n in (registrant, filed_as) if n}
    seen: set[tuple[str, str]] = set()
    kept: list[ListedRow] = []
    for row in rows:
        key = _row_key(row.name, row.jurisdiction)
        if not normalise_name(row.name) or key[0] in own or key in seen:
            continue
        seen.add(key)
        kept.append(row)
    return kept, prose


def _row_key(name: str, jurisdiction: str | None) -> tuple[str, str]:
    return _full_key(name), _collapse(jurisdiction or "").casefold()


def _omission_sentence(prose: str) -> str | None:
    """The exhibit's own statement that it omits insignificant subsidiaries, verbatim (cut at
    :data:`_MAX_STATEMENT`), or None. A sentence that says so is preferred; a heading naming the
    list as significant subsidiaries is the fallback. A statement set across text blocks ("List of
    Significant" / "Subsidiaries of Visa Inc.") is returned as the blocks it spans."""
    lines = prose.splitlines()
    sentences = [_collapse(x) for line in lines for x in _SENTENCE_END.split(line) if x.strip()]
    for pattern in (_OMISSION, _SIGNIFICANT_HEADING):
        for sentence in sentences:
            if pattern.search(sentence):
                return _cut(sentence)
    starts: list[int] = []
    pos = 0
    for line in lines:
        starts.append(pos)
        pos += len(line) + 1
    joined = " ".join(lines)
    for pattern in (_OMISSION, _SIGNIFICANT_HEADING):
        m = pattern.search(joined)
        if m is not None:
            first = bisect.bisect_right(starts, m.start()) - 1
            last = bisect.bisect_right(starts, max(m.end() - 1, m.start())) - 1
            return _cut(" ".join(lines[first:last + 1]))
    return None


def _cut(statement: str) -> str:
    if len(statement) <= _MAX_STATEMENT:
        return statement
    return statement[:_MAX_STATEMENT].rsplit(" ", 1)[0] + " …"


def name_in_force(history: RegistrantHistory, day: date | None) -> str | None:
    """The registrant's name ON ``day``: the earliest former-name span that ends on or after it,
    else the current name (today's when ``day`` is None). A read at a past cut must not take a
    later name (Codex, round 1 of #1152: Oruka Therapeutics filed as "ARCA biopharma, Inc." until
    2024-08-30).

    A day between two spans takes the NEXT span's name (the rename came before its first filing),
    and a day before the first span takes the first name: neither is today's (review round 2 of
    #1152 — ORKA's 2003-02-01, between HYSEQ's and NUVELO's spans, read "Oruka"). A span's start is
    not read, so EDGAR's inverted rows (a start after the end) cannot hide a span.
    `mechanical._former_name_flags` keeps the containing-span rule and its gap; B's to change."""
    if day is not None:
        later = [r for r in history.former if r.to_date >= day]
        if later:
            return min(later, key=lambda r: r.to_date).name
    return history.current or None


def read_exhibit21(edgar: EdgarClient, http: CachedHttp, cik: int | str, *,
                   through: date | None = None) -> Exhibit21Read:
    """The Exhibit 21 of the filer's newest original 10-K filed by ``through`` (any day if None).

    ``http`` is the SEC client ``edgar`` reads through (the archive documents are fetched with it,
    cached forever: a filed exhibit is immutable)."""
    cik10 = pad_cik(cik)
    # a cut in the past reads back far enough to reach that year's 10-K, beyond the recent page
    since = None if through is None else through - timedelta(days=_TENK_LOOKBACK_DAYS)
    try:
        tenks = [f for f in edgar.recent_filings(cik10, forms=("10-K",), since=since)
                 if through is None or f.filing_date <= through]
        # the same submissions document `recent_filings` just read: a cache hit
        history = edgar.registrant_history(cik10)
    except (HttpError, ValueError) as exc:
        return Exhibit21Read(cik=cik10, status="unread",
                             note=f"the submissions document for CIK{cik10} could not be read: "
                                  f"{exc}")
    registrant = name_in_force(history, through)
    if not tenks:
        window = (f"filed by {through}, in the {_TENK_LOOKBACK_DAYS} days before it"
                  if through else "on the submissions document's recent page")
        return Exhibit21Read(cik=cik10, registrant=registrant, status="no_10k",
                             note=f"no original 10-K {window}")
    tenk = max(tenks, key=lambda f: f.filing_date)
    filed_as = name_in_force(history, tenk.filing_date)
    docs = ex21_documents(http, cik10, tenk.accession)
    base = {"cik": cik10, "registrant": registrant, "filed_as": filed_as,
            "accession": tenk.accession, "filing_date": tenk.filing_date}
    if docs is None:
        return Exhibit21Read(**base, status="unread",
                             note=f"the SGML header of 10-K {tenk.accession} could not be read")
    if not docs:
        return Exhibit21Read(**base, status="no_ex21",
                             note=f"10-K {tenk.accession}'s SGML header types no EX-21 document. "
                                  f"An exhibit incorporated by reference to another filing, "
                                  f"filed in a 10-K/A, or in a format other than text is not "
                                  f"seen")
    texts: list[tuple[str, str, str]] = []
    for ty, url in docs:
        try:
            texts.append((ty, url, http.get_text(url, ttl_seconds=None)))
        except (HttpError, ValueError) as exc:
            return Exhibit21Read(**base, status="unread", exhibit_urls=tuple(u for _, u in docs),
                                 note=f"{ty} at {url} could not be read: {exc}")
    return bind_exhibit21(cik10, tenk.accession, tenk.filing_date, texts, registrant=registrant,
                          filed_as=filed_as)


def bind_exhibit21(cik: str, accession: str, filing_date: date,
                   documents: list[tuple[str, str, str]], *,
                   registrant: str | None, filed_as: str | None = None) -> Exhibit21Read:
    """The read of one 10-K's Exhibit 21 documents, each ``(type, url, text)`` as EDGAR serves
    it: every listed name bound to its ``source_ref``. No HTTP here (:func:`read_exhibit21`
    fetches); a row listed verbatim in two of the filing's exhibits is kept once, at its first."""
    names: list[Subsidiary] = []
    prose_parts: list[str] = []
    seen: set[tuple[str, str]] = set()
    for ty, url, doc in documents:
        rows, prose = parse_exhibit21(doc, registrant=registrant, filed_as=filed_as)
        prose_parts.append(prose)
        ref = f"10-K {accession} {ty} · {url}"
        for row in rows:
            key = _row_key(row.name, row.jurisdiction)
            if key in seen:
                continue
            seen.add(key)
            names.append(Subsidiary(name=row.name, jurisdiction=row.jurisdiction,
                                    stated_percent=row.stated_percent, source_ref=ref))
    prose_all = "\n".join(prose_parts)
    common = {"cik": pad_cik(cik), "registrant": registrant, "filed_as": filed_as,
              "accession": accession,
              "filing_date": filing_date,
              "exhibit_urls": tuple(u for _, u, _ in documents),
              "states_omission": _omission_sentence(prose_all),
              "names_affiliates": _AFFILIATES.search(prose_all) is not None}
    if not names:
        return Exhibit21Read(**common, status="no_names",
                             note="the exhibit was read and no listed name was found in it: a "
                                  "parse failure, not an empty list")
    return Exhibit21Read(**common, status="listed", names=tuple(names))


def _confirms(sub: Subsidiary, read: Exhibit21Read) -> bool:
    share = sub.stated_percent
    return not read.names_affiliates and (share is None or share > 50)


def match_entity(entity: str, read: Exhibit21Read) -> EntityMatch:
    """``entity`` against ``read``'s list, at the tightest tier it reaches (see module doc).

    A name listed exactly is that listing, even when it shares the registrant's base name ("Eli
    Lilly and Company Limited" is Lilly's UK subsidiary, not Lilly); otherwise an entity that
    normalises to the registrant, under its name at the cut or the one its 10-K was filed under,
    is the registrant."""
    partial = read.states_omission is not None
    want = _collapse(entity)
    for sub in read.names:
        if _collapse(sub.name) == want:
            return EntityMatch(entity=entity, tier="exact", listed=sub,
                               list_states_omission=partial, confirms_own=_confirms(sub, read))
    key = normalise_name(entity)
    if key and key in {normalise_name(n) for n in (read.registrant, read.filed_as) if n}:
        return EntityMatch(entity=entity, tier="registrant", list_states_omission=partial,
                           confirms_own=True)
    if read.status != "listed":
        return EntityMatch(entity=entity, tier=read.status, list_states_omission=partial)
    if key:
        for sub in read.names:
            if normalise_name(sub.name) == key:
                return EntityMatch(entity=entity, tier="normalised", listed=sub,
                                   list_states_omission=partial,
                                   confirms_own=_confirms(sub, read))
        want_toks = key.split()
        for sub in read.names:
            toks = normalise_name(sub.name).split()
            if len(toks) > len(want_toks) and toks[:len(want_toks)] == want_toks:
                return EntityMatch(entity=entity, tier="word_prefix", listed=sub,
                                   list_states_omission=partial)
    return EntityMatch(entity=entity, tier="not_listed", list_states_omission=partial)
