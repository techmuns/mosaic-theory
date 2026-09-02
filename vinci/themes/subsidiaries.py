"""EDGAR **Exhibit 21 — Subsidiaries of the Registrant** — complete source for control pairs.

WHY THIS EXISTS. `flag_intra_population_control` reads an issuer's driver-exposure EXTRACTS and can
only see a subsidiary that happens to be cited exchange-qualified — true of 2 of 745 rows in the
ai-compute-platform scan. Its coverage is UNKNOWN, and a scan reporting no pairs could mean
near-blindness. Exhibit 21 is the filed, structured answer: BTBT's is nine rows, one of which reads
``WhiteFiber, Inc. | Cayman Islands | 70.5%``.

WHAT IT REFUSES. It returns the filed rows and never decides anything. Which side of a control pair
carries a driver's exposure stays an adjudication (assemble-not-conclude).
"""
from __future__ import annotations

import html
import json
import re
from typing import Any

from vinci.netcache import CachedHttp

_SUB_API = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
_ARCHIVE = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/"
# Filename alone is NOT enough: WULF's SOX certification `wulf-20251231xex321.htm` matches any loose
# ex-21 pattern (the "21" falls inside "321"), while its real exhibit is `exhibit211-listofsubsidi`.
# Every candidate is therefore confirmed by CONTENT before it is used.
# `ex(?:hibit)?[-_.]?21` cannot match "ex321" (Exhibit 32.1) — after "ex" comes "3", so the
# literal "21" fails. An earlier extra [^0-9] prefix guard was therefore useless AND harmful: it
# rejected BTBT's real exhibit `ea027962101ex21.htm`, whose "ex" is preceded by a digit.
_EX21_NAME = re.compile(r"ex(?:hibit)?[-_.]?21(?:[-_.]|\d|$)", re.I)
_HEADERISH = re.compile(r"^(?:name|entity|subsidiar\w*|legal entity|name of subsidiar\w*|"
                        r"subsidiaries of[\w\s.,]*)$", re.I)
# NOT PARSED, DELIBERATELY: some registrants file Exhibit 21 as running text, not a table. WULF's
# is two <p> tags reading "Abernathy Data LLC 50.1% Delaware Akela Data LLC 100% Delaware ...".
# Splitting on the percentage leaves "JURISDICTION NAME" segments whose boundary cannot be found
# without enumerating jurisdictions or guessing a word count -- a first attempt returned the table
# HEADER as an entity name. A parser that guesses here fabricates ownership data, so this returns
# NOTHING for that layout and says so.
_PCT = re.compile(r"^\s*(?:approximately\s*)?(\d{1,3}(?:\.\d+)?)\s*%\s*$", re.I)
_ROW = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S | re.I)
_CELL = re.compile(r"<t[dh][^>]*>(.*?)</t[dh]>", re.S | re.I)


def _text(fragment: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def parse_exhibit_21(document: str) -> list[tuple[str, float | None]]:
    """Rows of an Exhibit 21 as ``(entity name, percent voting owned or None)``.

    TABLE LAYOUTS ONLY. A running-text exhibit yields ``[]`` — see the note above; that is an
    unparsed document, never an empty subsidiary list, and the caller must not read it as one.

    A row with no stated percentage yields ``None`` rather than an assumed 100% — many registrants
    omit the column entirely for wholly-owned subsidiaries, and guessing there would be exactly the
    fabricated value CLAUDE.md forbids. The caller decides what an unstated percentage means.
    """
    out: list[tuple[str, float | None]] = []
    for row in _ROW.findall(document):
        cells = [c for c in (_text(x) for x in _CELL.findall(row)) if c]
        if not cells:
            continue
        name = cells[0]
        if not name or len(name) > 200 or _HEADERISH.match(name):
            continue                      # header row (CORZ's reads "Name of Subsidiary")
        pct: float | None = None
        for cell in cells[1:]:
            if (m := _PCT.match(cell)) is not None:
                pct = float(m.group(1))
                break
        out.append((name, pct))
    return out


def _pick_exhibit_21(http: CachedHttp, cik: int, accession: str, names: list[str]) -> str | None:
    base = _ARCHIVE.format(cik=cik, acc=accession.replace("-", ""))
    for name in names:
        if not _EX21_NAME.search(name) or not name.lower().endswith((".htm", ".html", ".txt")):
            continue
        body = http.get_text(base + name)
        if "subsidiar" in body.lower():    # CONTENT confirms; the filename only proposes
            return body
    return None


def subsidiaries_of(http: CachedHttp, cik: str | int, *, forms: tuple[str, ...] = ("10-K", "20-F")
                    ) -> list[tuple[str, float | None]]:
    """Exhibit 21 rows from the registrant's most recent annual report, or ``[]`` if it filed none.

    An empty list means NO EXHIBIT WAS FOUND — never "no subsidiaries". Smaller registrants omit
    Exhibit 21 when they have none to report, and the two cases are not distinguishable here.
    """
    n = int(str(cik).lstrip("0") or 0)
    sub: dict[str, Any] = json.loads(http.get_text(_SUB_API.format(cik=n)))
    recent = sub.get("filings", {}).get("recent", {})
    forms_list = recent.get("form", [])
    for i, form in enumerate(forms_list):
        if form not in forms:
            continue
        accession = recent["accessionNumber"][i]
        index = json.loads(http.get_text(
            _ARCHIVE.format(cik=n, acc=accession.replace("-", "")) + "index.json"))
        names = [it["name"] for it in index["directory"]["item"]]
        if (doc := _pick_exhibit_21(http, n, accession, names)) is not None:
            return parse_exhibit_21(doc)
        return []                          # most recent annual report only — older ones are stale
    return []
