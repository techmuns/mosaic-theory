"""(RC-1 B) DETERMINISTIC 10-Q/10-K section parser — heading/anchor-targeted, never whole-document,
never an LLM. Extracts, each source-bound to the filing: the going-concern / substantial-doubt note,
the FILING-BASIS near-term maturity wall (distinct from the CIQ panel), customer concentration, and
purchase/capital commitments.

Fail-loud (the PR-2 lesson): a section with no anchored pattern is absent + a qa_flag 'no anchored
pattern matched — {section}', never a guessed number, never an analyst caveat. Text is read
pre-normalized (vinci.graph.filings.normalize_text). Coverage is partial beyond the pinned names.
"""
from __future__ import annotations

import re

from vinci.dossier.schemas import (
    Commitment,
    ConcentrationCustomer,
    CustomerConcentration,
    DebtTranche,
    FilingSectionExtract,
    GoingConcern,
    MaturityWall,
)
from vinci.resolver.index import pad_cik

_ARCHIVE = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{doc}"


def filing_url(cik: str | int, accession: str, doc: str) -> str:
    """The primary-document URL for a 10-Q/10-K accession — the text the parser reads."""
    return _ARCHIVE.format(cik=int(pad_cik(str(cik))), acc=accession.replace("-", ""), doc=doc)


def _money(s: str) -> float | None:
    try:
        return float(s.replace(",", "").replace("$", "").strip())
    except ValueError:
        return None


def _sentence(text: str, pos: int, *, cap: int = 400) -> str:
    """The verbatim sentence around ``pos``, single-spaced, ≤cap chars."""
    lo = text.rfind(". ", max(0, pos - cap), pos)
    lo = (lo + 2) if lo != -1 else max(0, pos - cap)
    hi = text.find(". ", pos)
    hi = (hi + 1) if hi != -1 else min(len(text), pos + cap)
    return " ".join(text[lo:hi].split())[:cap].strip()


# --- (1) going concern ---------------------------------------------------------------------------
_SUBDOUBT = re.compile(r"raise\s+substantial\s+doubt\s+about\s+[^.]*?going\s+concern", re.I)
_PLANS = re.compile(r"(plans?\s+to\s+alleviate[^.]*\.)", re.I)


def _going_concern(text: str, src: str) -> GoingConcern | None:
    m = _SUBDOUBT.search(text)
    if m is None:
        return None
    pm = _PLANS.search(text, m.end(), m.end() + 900)
    return GoingConcern(
        substantial_doubt=True, verbatim=_sentence(text, m.start()),
        plans=" ".join(pm.group(1).split())[:300] if pm else "", source_ref=src,
    )


# --- (2) filing-basis maturity wall --------------------------------------------------------------
_WITHIN_12M = re.compile(
    r"\$\s*([\d,.]+)\s*million\s+due\s+within\s+the\s+next\s+12\s+months", re.I)
_TRANCHE = re.compile(
    r"\b(bond\s+payable|convertible\s+loan|convertible\s+note|term\s+loan|note\s+payable|"
    r"senior\s+notes?|revolving\s+(?:credit\s+)?facility|credit\s+facility)\b[^.]*?"
    r"\$\s*([\d,.]+)\s*million[^.]*?matures\s+in\s+([A-Za-z]+\s+20\d\d)",
    re.I,
)
# a debt section is LOCATED when any of these instrument anchors appear — so a filing that has debt
# but no '≤12m wall' sentence is state='not_stated' (KNOWN), distinct from no-debt-section UNKNOWN.
_DEBT_SECTION = re.compile(
    r"\b(term\s+loan|senior\s+notes?|convertible\s+(?:loan|note)|long[- ]term\s+debt|"
    r"notes?\s+payable|revolv\w*|credit\s+facility|bond\s+payable|borrowings)\b",
    re.I,
)
_NOT_STATED_NOTE = "no near-term wall stated in filing — composition table present; see CIQ panel"


def _maturity_wall(text: str, src: str) -> MaturityWall | None:
    wm = _WITHIN_12M.search(text)
    if wm is not None:  # state='located' — a ≤12m-wall statement was found
        anchor = wm.start()
        tranches: list[DebtTranche] = []
        for tm in _TRANCHE.finditer(text[max(0, anchor - 200):anchor + 500]):
            amt = _money(tm.group(2))
            if amt is None:
                continue
            tranches.append(DebtTranche(
                name=" ".join(tm.group(1).split()).lower(), amount=amt,
                maturity=tm.group(3).strip(),
                verbatim=" ".join(tm.group(0).split())[:200], source_ref=src,
            ))
        return MaturityWall(
            within_12m_total=_money(wm.group(1)), tranches=tranches, state="located", note="",
            verbatim=_sentence(text, anchor), source_ref=src,
        )
    if _DEBT_SECTION.search(text):  # debt section present, but NO ≤12m wall stated — a KNOWN
        return MaturityWall(
            within_12m_total=None, tranches=[], state="not_stated", note=_NOT_STATED_NOTE,
            verbatim="", source_ref=src,
        )
    return None  # no debt section located at all — true UNKNOWN


# --- (3) customer concentration ------------------------------------------------------------------
# A customer LABEL is a short identifier (A / B / C / 1 / 2) — NOT a word: this rejects the
# 'no customer exceeded 10%' phrasing (a healthy roster) that a greedy [A-Z0-9]+ read as 'Customer
# EXCEEDED 10%' (a fabricated concentration). No re.I on the label ⇒ 'exceeded' cannot match.
_CUST = re.compile(r"[Cc]ustomer\s+([A-Z]{1,2}|\d{1,2})\b\s+([\d.]+)\s*%(?:\s+([\d.]+)\s*%)?")
# Prose EXACT: 'The {Named Customer} (ABBR) represented 15.2% and 15.4%' — a stated %, preferred
# over the floor lead-in for the same customer (extract the disclosed value, never understate).
_CUST_EXACT = re.compile(
    r"[Tt]he\s+([A-Z][A-Za-z.&'\s]{3,60}?)(?:\s*\([^)]{1,20}\))?\s+represented\s+"
    r"([\d.]+)\s*%(?:\s+and\s+([\d.]+)\s*%)?")
# Prose FLOOR: 'a single/one {desc} customer exceeded 10%' — a disclosed FLOOR (value_kind='floor').
# Only 'a single'/'one' (a POSITIVE concentration) — never 'No other/Commercial customer exceeded'.
_CUST_FLOOR = re.compile(
    r"(?:a\s+single|one)\s+([A-Za-z][\w\s]{0,40}?)\s+customer\s+(?:that\s+)?exceeded\s+"
    r"([\d.]+)\s*%[^.]{0,30}?revenue", re.I)
_TERMS = re.compile(
    r"(purchase\s+order|minimum\s+(?:volume|purchase)|take[- ]or[- ]pay|"
    r"binding\s+(?:volume|purchase))[^.]{0,120}",
    re.I,
)


def _concentration(text: str, src: str) -> CustomerConcentration | None:
    custs: list[ConcentrationCustomer] = []
    seen: set[str] = set()
    # (1) table form — 'Customer A 52 % 31 %' → exact
    for m in _CUST.finditer(text):
        name = f"Customer {m.group(1).upper()}"
        pct = _money(m.group(2))
        if name in seen or pct is None or pct > 100:
            continue
        seen.add(name)
        custs.append(ConcentrationCustomer(
            name=name, pct=pct, prior_pct=_money(m.group(3)) if m.group(3) else None,
            value_kind="exact",
        ))
    # (2) prose EXACT — 'The {Named} represented 15.2% and 15.4%' → exact (preferred over floor)
    if not custs:
        for m in _CUST_EXACT.finditer(text):
            pct = _money(m.group(2))
            name = " ".join(m.group(1).split())
            if pct is None or pct > 100 or name in seen:
                continue
            seen.add(name)
            custs.append(ConcentrationCustomer(
                name=name, pct=pct, prior_pct=_money(m.group(3)) if m.group(3) else None,
                value_kind="exact",
            ))
    # (3) prose FLOOR — 'a single {desc} customer exceeded 10%' → floor (only if no exact figure)
    if not custs:
        fm = _CUST_FLOOR.search(text)
        if fm is not None and (pct := _money(fm.group(2))) is not None:
            custs.append(ConcentrationCustomer(
                name=" ".join(fm.group(1).split()) + " customer", pct=pct, prior_pct=None,
                value_kind="floor",
            ))
    if not custs:
        return None
    tm = _TERMS.search(text)
    return CustomerConcentration(
        customers=custs, top5_pct=None,
        terms=" ".join(tm.group(0).split())[:200] if tm else "", source_ref=src,
    )


# --- (4) purchase / capital commitments ----------------------------------------------------------
_COMMIT = re.compile(
    r"\$\s*([\d,.]+)\s*million\s+(?:in|of)\s+(purchase|capital)\s+commitments"
    r"(?:\s+with\s+\$\s*([\d,.]+)\s*million\s+due\s+within)?",
    re.I,
)


def _commitments(text: str, src: str) -> list[Commitment]:
    out: list[Commitment] = []
    for m in _COMMIT.finditer(text):
        amt = _money(m.group(1))
        if amt is None:
            continue
        out.append(Commitment(
            kind=m.group(2).lower(), amount=amt,
            within_12m=_money(m.group(3)) if m.group(3) else None,
            verbatim=_sentence(text, m.start(), cap=240), source_ref=src,
        ))
    return out


def parse_filing_sections(text: str, *, source_ref: str) -> FilingSectionExtract:
    """Parse a 10-Q/10-K's normalized text into a source-bound FilingSectionExtract. Each absent
    section fails loud with a qa_flag — a miss is UNKNOWN, never a fabricated value."""
    wall = _maturity_wall(text, source_ref)
    conc = _concentration(text, source_ref)
    flags: list[str] = []
    if wall is None:
        flags.append(f"no anchored pattern matched — maturity wall: {source_ref}")
    if conc is None:
        flags.append(f"no anchored pattern matched — customer concentration: {source_ref}")
    return FilingSectionExtract(
        source_ref=source_ref, going_concern=_going_concern(text, source_ref),
        maturity_wall=wall, concentration=conc, commitments=_commitments(text, source_ref),
        qa_flags=flags,
    )
