"""What a listed line IS, in the issuer's own words — the 12(b) title on its latest cover page.

THE REFERENCE FEED TYPES SOME DEBT AS COMMON STOCK. Of the 5,324 lines Polygon's 2026-10-17 pull
types ``CS``, 58 name themselves notes, debentures or bonds — ADAMK ("Adamas Trust, Inc. 9.600%
Senior Notes Due 2031"), TMUSI ("T-Mobile US, Inc. 5.500% Senior Notes due June 2070"), XELLL — so
the universe's instrument allowlist cannot see them. The issuer can: every security registered
under Section 12(b) is listed on the cover page of its periodic filings, its inline-XBRL
``dei:TradingSymbol`` and ``dei:Security12bTitle`` in one context — a structured SEC field, keyed
by the symbol, in the issuer's own words.

IT CANNOT SEE A LINE LISTED SINCE THAT COVER. ADAMK itself is the case: its 8-A12B is dated
2026-08-14 and Adamas's latest 10-Q 2026-07-31, so until the next periodic report the cover says
nothing about it and nothing here excludes it.

TWO CLASSES ARE READ OUT OF IT, AND NOTHING ELSE.
- DEBT: a title that names notes, debentures or bonds. Every one of the 21 debt titles on the
  frozen covers does, and none of the 2,461 titles on the covers of the 2026-10-16 population's
  2,065 members names one alongside common shares or names only a maturity, so no rule is carried
  for either.
- PREFERRED: a title that names preferred (or preference) stock, ONLY when the same cover registers
  the issuer's common under ANOTHER symbol. The feed types MCHPP — Microchip's "Depositary Shares,
  each representing a 1/20th interest in a share of 7.50% Series A Mandatory Convertible Preferred
  Stock" — ``CS``, and it sat in the primary population on 2026-08-24 and 2026-09-22; the
  allowlist already excludes a line the feed types ``PFD`` (operator ruling 2026-10-27: enforcing
  that intent, not a new policy). The second condition is not decoration: Mission Produce's real
  cover tags AVO, its common, to "Series A Junior Participating Preferred Stock" (its rights plan)
  and leaves its common's title without a symbol. A preferred title alone would delete a common
  stock; a cover that shows the common trading under another symbol cannot.
LP units ("Depositary Units … Representing Limited Partner Interests"), ADSs of units and anything
untitled stay what the rest of the builder says they are.

A TWIN, ON PURPOSE. ``vinci.theme_intelligence.securities.parse_cover`` reads the same tags, but
the isolation boundary forbids the fund importing that package and lets it import only shared
plumbing (``tests/test_theme_intelligence_isolation.py``), so the two cannot share one parser. This
one is the narrower: it answers only "how does the issuer register THIS symbol".
"""

from __future__ import annotations

import html as htmllib
import re
from dataclasses import dataclass
from datetime import date
from typing import Any

#: the periodic reports whose cover page lists every 12(b) security; an amendment's cover is the
#: issuer's statement on its own date, so it counts like the original
PERIODIC_FORMS = frozenset({"10-K", "10-Q", "20-F", "40-F", "10-K/A", "10-Q/A", "20-F/A",
                            "40-F/A", "10-KT", "10-QT"})

_IX = re.compile(r"<ix:nonnumeric\b([^>]*)>(.*?)</ix:nonnumeric>", re.I | re.S)
_COVER_TAGS = ("dei:TradingSymbol", "dei:Security12bTitle")
_DEBT = re.compile(r"\bnotes?\b|\bdebentures?\b|\bbonds?\b", re.I)
_PREFERRED = re.compile(r"\bpreferred\b|\bpreference\b", re.I)
_COMMON = re.compile(r"\bcommon\b|\bordinary\s+shares?\b", re.I)


@dataclass(frozen=True)
class RegisteredLine:
    """One symbol as the issuer's cover page registers it, with the filing that says so."""

    symbol: str
    title: str | None
    form: str
    filed: date
    accession: str
    #: the same cover registers a common class under ANOTHER symbol
    common_elsewhere: bool = False

    @property
    def is_debt(self) -> bool:
        return is_debt_title(self.title)

    @property
    def excluded_class(self) -> str | None:
        """``"debt"`` or ``"preferred"`` when the issuer's own title says the line is not its
        common equity, else None. Preferred needs the common to be registered elsewhere on the
        cover (see the module docstring: AVO)."""
        if self.is_debt:
            return "debt"
        if self.common_elsewhere and bool(self.title and _PREFERRED.search(self.title)):
            return "preferred"
        return None


def is_debt_title(title: str | None) -> bool:
    """A registered title that names a debt security — never an absent one (an untitled line is
    not evidence of anything)."""
    return bool(title and _DEBT.search(title))


def is_common_title(title: str | None) -> bool:
    """A registered title of common or ordinary equity (no title on the 2026-10-16 population's
    covers names both common and preferred, so none is carved out)."""
    return bool(title and _COMMON.search(title))


def symbol_key(symbol: str) -> str:
    """One spelling for a symbol written three ways: SEC's ``UHAL-B``, a cover's ``UHAL.B`` or
    Brown-Forman's own ``BFB``."""
    return re.sub(r"[^A-Z0-9]", "", symbol.upper())


def cover_lines(doc_html: str) -> list[tuple[str | None, str | None]]:
    """``(trading symbol, 12(b) title)`` per XBRL context of an inline-XBRL periodic filing — each
    registered class carries its own context. Either half may be None: Brunswick tags its common's
    title and symbol in two different contexts."""
    by_ctx: dict[str, dict[str, str]] = {}
    for m in _IX.finditer(doc_html):
        attrs = m.group(1)
        nm = re.search(r'\bname="([^"]+)"', attrs)
        if not nm or nm.group(1) not in _COVER_TAGS:
            continue
        ctx = re.search(r'\bcontextref="([^"]+)"', attrs, re.I)
        text = " ".join(htmllib.unescape(re.sub(r"<[^>]+>", " ", m.group(2))).split())
        by_ctx.setdefault(ctx.group(1) if ctx else "?", {}).setdefault(nm.group(1), text)
    out: list[tuple[str | None, str | None]] = []
    for d in by_ctx.values():
        sym = (d.get("dei:TradingSymbol") or "").strip().strip("\"'“”‘’").strip()
        out.append((sym or None, d.get("dei:Security12bTitle") or None))
    return out


def periodic_filings(submissions: dict[str, Any],
                     as_of: date) -> list[tuple[str, date, str, str]]:
    """``(form, filed, accession, primary document)`` of the issuer's periodic reports filed on or
    before ``as_of``, newest first, from the submissions index's RECENT block. The older pages are
    not walked: a filer still trading has a periodic report in its recent block, and one that has
    none has no current cover to read."""
    recent = submissions.get("filings", {}).get("recent", {})
    rows = zip(recent.get("form", []), recent.get("filingDate", []),
               recent.get("accessionNumber", []), recent.get("primaryDocument", []), strict=False)
    periodic = sorted(((date.fromisoformat(d), f, a, p) for f, d, a, p in rows
                       if f in PERIODIC_FORMS and p and date.fromisoformat(d) <= as_of),
                      reverse=True)
    return [(form, filed, acc, doc) for filed, form, acc, doc in periodic]


#: the annual reports only a foreign private issuer files
FOREIGN_PRIVATE_ISSUER_FORMS = frozenset({"20-F", "40-F"})


def latest_report(submissions: dict[str, Any], as_of: date) -> tuple[str, date, str] | None:
    """``(form, filed, accession)`` of the issuer's latest periodic report filed on or before
    ``as_of`` — never an amendment, which restates an earlier period and so says nothing about how
    the issuer files NOW (Enbridge filed 40-F to 2017 and 10-K since). None when there is none."""
    for form, filed, acc, _doc in periodic_filings(submissions, as_of):
        if not form.endswith("/A"):
            return form, filed, acc
    return None


def latest_periodic(submissions: dict[str, Any],
                    as_of: date) -> tuple[str, date, str, str] | None:
    """The newest of :func:`periodic_filings`, or None when there is none."""
    filings = periodic_filings(submissions, as_of)
    return filings[0] if filings else None


def registered_line(doc_html: str, ticker: str, *, form: str, filed: date,
                    accession: str) -> RegisteredLine | None:
    """How the cover in ``doc_html`` registers ``ticker``, or None when the symbol is not on it."""
    return match_line(cover_lines(doc_html), ticker, form=form, filed=filed, accession=accession)


def match_line(lines: list[tuple[str | None, str | None]], ticker: str, *, form: str,
               filed: date, accession: str) -> RegisteredLine | None:
    """``ticker``'s entry among a cover's ``lines``. A cover can tag one symbol in two contexts, so
    a symbol is excluded only when EVERY context carrying it says so: any other title wins."""
    key = symbol_key(ticker)
    elsewhere = any(sym and symbol_key(sym) != key and is_common_title(title)
                    for sym, title in lines)
    found = [RegisteredLine(symbol=sym, title=title, form=form, filed=filed, accession=accession,
                            common_elsewhere=elsewhere)
             for sym, title in lines if sym and symbol_key(sym) == key]
    return next((r for r in found if r.excluded_class is None), found[0] if found else None)
