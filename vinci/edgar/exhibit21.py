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
- An exhibit with no table gives one name per text line that ends in a corporate suffix ("Inc.",
  "LLC", "Ltd" …) once a trailing parenthetical is set aside as its jurisdiction ("Target Brands,
  Inc. (MN)").
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

Every listed name carries its ``source_ref``: the form, the accession, the exhibit's own type and
its URL.
"""

from __future__ import annotations

import bisect
import html
import re
import unicodedata
from datetime import date
from typing import Literal, NamedTuple

from bs4 import BeautifulSoup
from pydantic import BaseModel

from vinci.edgar.client import EdgarClient
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
}, key=len, reverse=True))

#: A header cell's vocabulary: a column title ("Name of Subsidiary", "Entity", "Jurisdiction") or a
#: section title ("Operating Subsidiaries", TJX's), never a company.
_HEADER_CELL = re.compile(
    r"^(?:(?:legal|company|entity|exact)\s+)?names?\b|^subsidiar(?:y|ies)\b|^entit(?:y|ies)\b"
    r"|\bsubsidiar(?:y|ies)$|jurisdiction|incorporat|\borgani[sz]ation\b|^state\b|^country\b"
    r"|percent|owner|^%", re.I)
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
    #: The filer's current registrant name (EDGAR's submissions document), or None when unread.
    registrant: str | None = None
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


# --- normalisation ------------------------------------------------------------------------------

def _collapse(s: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", s).split())


def _tokens(name: str) -> list[str]:
    """The name's words, casefolded, punctuation set aside, a trailing parenthetical dropped."""
    s = unicodedata.normalize("NFKC", name).casefold()
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


def _ends_in_suffix(name: str) -> bool:
    toks = _tokens(name)
    return any(len(toks) > len(s) and tuple(toks[-len(s):]) == s for s in _SUFFIXES)


# --- the exhibit ---------------------------------------------------------------------------------

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
            if _EX21_TYPE.fullmatch(ty.strip()) and fn.lower().endswith(_TEXT_DOC)]


class ListedRow(NamedTuple):
    """One row of an Exhibit 21 as parsed, before it is bound to its filing."""

    name: str
    jurisdiction: str | None
    stated_percent: float | None


def _split_jurisdiction(line: str) -> tuple[str, str | None]:
    m = _TRAILING_PAREN.search(line)
    if m and m.start() > 0:
        return line[:m.start()].strip(), (m.group(1).strip() or None)
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
        if _HEADER_CELL.search(name) and not _ends_in_suffix(name):
            continue  # a column or section title
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
        if name and _ends_in_suffix(name):
            out.append(ListedRow(name, juris, _percent(line)))
    return out


def parse_exhibit21(doc: str, *, registrant: str | None = None) -> tuple[list[ListedRow], str]:
    """``(rows, prose)`` of one Exhibit 21 document: each listed row in the exhibit's order, and the
    exhibit's text outside its tables, one line per text block (where it states what it omits).

    The registrant's own name is dropped. Names are deduplicated by their normalised key, first
    listing kept."""
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
    own = normalise_name(registrant) if registrant else None
    seen: set[str] = set()
    kept: list[ListedRow] = []
    for row in rows:
        key = normalise_name(row.name)
        if not key or key == own or key in seen:
            continue
        seen.add(key)
        kept.append(row)
    return kept, prose


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


def read_exhibit21(edgar: EdgarClient, http: CachedHttp, cik: int | str, *,
                   through: date | None = None) -> Exhibit21Read:
    """The Exhibit 21 of the filer's newest original 10-K filed by ``through`` (any day if None).

    ``http`` is the SEC client ``edgar`` reads through (the archive documents are fetched with it,
    cached forever: a filed exhibit is immutable)."""
    cik10 = pad_cik(cik)
    tenks = [f for f in edgar.recent_filings(cik10, forms=("10-K",))
             if through is None or f.filing_date <= through]
    # the same submissions document `recent_filings` just read: a cache hit, not a second fetch
    registrant = edgar.registrant_history(cik10).current or None
    if not tenks:
        return Exhibit21Read(cik=cik10, registrant=registrant, status="no_10k",
                             note="no 10-K on the submissions document's recent page"
                                  + (f" filed by {through}" if through else ""))
    tenk = max(tenks, key=lambda f: f.filing_date)
    docs = ex21_documents(http, cik10, tenk.accession)
    base = {"cik": cik10, "registrant": registrant, "accession": tenk.accession,
            "filing_date": tenk.filing_date}
    if docs is None:
        return Exhibit21Read(**base, status="unread",
                             note=f"the SGML header of 10-K {tenk.accession} could not be read")
    if not docs:
        return Exhibit21Read(**base, status="no_ex21",
                             note=f"10-K {tenk.accession}'s header types no document EX-21")
    texts: list[tuple[str, str, str]] = []
    for ty, url in docs:
        try:
            texts.append((ty, url, http.get_text(url, ttl_seconds=None)))
        except (HttpError, ValueError) as exc:
            return Exhibit21Read(**base, status="unread", exhibit_urls=tuple(u for _, u in docs),
                                 note=f"{ty} at {url} could not be read: {exc}")
    return bind_exhibit21(cik10, tenk.accession, tenk.filing_date, texts, registrant=registrant)


def bind_exhibit21(cik: str, accession: str, filing_date: date,
                   documents: list[tuple[str, str, str]], *,
                   registrant: str | None) -> Exhibit21Read:
    """The read of one 10-K's Exhibit 21 documents, each ``(type, url, text)`` as EDGAR serves
    it: every listed name bound to its ``source_ref``. No HTTP here (:func:`read_exhibit21`
    fetches); a name listed in two of the filing's exhibits is kept once, at its first."""
    names: list[Subsidiary] = []
    prose_parts: list[str] = []
    seen: set[str] = set()
    for ty, url, doc in documents:
        rows, prose = parse_exhibit21(doc, registrant=registrant)
        prose_parts.append(prose)
        ref = f"10-K {accession} {ty} · {url}"
        for row in rows:
            key = normalise_name(row.name)
            if key in seen:
                continue
            seen.add(key)
            names.append(Subsidiary(name=row.name, jurisdiction=row.jurisdiction,
                                    stated_percent=row.stated_percent, source_ref=ref))
    prose_all = "\n".join(prose_parts)
    common = {"cik": pad_cik(cik), "registrant": registrant, "accession": accession,
              "filing_date": filing_date,
              "exhibit_urls": tuple(u for _, u, _ in documents),
              "states_omission": _omission_sentence(prose_all),
              "names_affiliates": _AFFILIATES.search(prose_all) is not None}
    if not names:
        return Exhibit21Read(**common, status="no_names",
                             note="the exhibit was read and no listed name was found in it: a "
                                  "parse failure, not an empty list")
    return Exhibit21Read(**common, status="listed", names=tuple(names))


def match_entity(entity: str, read: Exhibit21Read) -> EntityMatch:
    """``entity`` against ``read``'s list, at the tightest tier it reaches (see module doc)."""
    partial = read.states_omission is not None
    if read.registrant and normalise_name(entity) == normalise_name(read.registrant):
        return EntityMatch(entity=entity, tier="registrant", list_states_omission=partial)
    if read.status != "listed":
        return EntityMatch(entity=entity, tier=read.status, list_states_omission=partial)
    want = _collapse(entity)
    for sub in read.names:
        if _collapse(sub.name) == want:
            return EntityMatch(entity=entity, tier="exact", listed=sub,
                               list_states_omission=partial)
    key = normalise_name(entity)
    if key:
        for sub in read.names:
            if normalise_name(sub.name) == key:
                return EntityMatch(entity=entity, tier="normalised", listed=sub,
                                   list_states_omission=partial)
        want_toks = key.split()
        for sub in read.names:
            toks = normalise_name(sub.name).split()
            if len(toks) > len(want_toks) and toks[:len(want_toks)] == want_toks:
                return EntityMatch(entity=entity, tier="word_prefix", listed=sub,
                                   list_states_omission=partial)
    return EntityMatch(entity=entity, tier="not_listed", list_states_omission=partial)
