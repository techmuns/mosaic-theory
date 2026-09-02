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
    DriverKind,
    FilingSectionExtract,
    GoingConcern,
    MaturityWall,
    OperatingDriver,
)
from vinci.edgar.going_concern import find_going_concern_statement
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
# THE DETECTION LIVES IN `vinci.edgar.going_concern`, shared with the ranker's structural demote.
# It used to be a local `raise substantial doubt about … going concern` match, which fired on the
# ASU 2014-15 EVALUATION sentence every filer writes — so TECX's page asserted substantial doubt
# for a company holding $227.1M and guiding runway into Q1 2029, and the synthesis then wrote a
# strongly-bearish verdict citing it. One detector, two consumers: the demote and the page must
# never disagree about whether a filer said this (the twin-drift class).
_PLANS = re.compile(r"(plans?\s+to\s+alleviate[^.]*\.)", re.I)


def _going_concern(text: str, src: str) -> GoingConcern | None:
    hit = find_going_concern_statement(text)
    if hit is None:
        return None
    pm = _PLANS.search(text, hit.start, hit.start + 900)
    return GoingConcern(
        substantial_doubt=True, verbatim=hit.sentence,
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


# --- (PR-B A2) MD&A results attribution — price/volume/mix causality -----------------------------
# The canonical MD&A shape, CONFIRMED across the cohort's cached 10-Qs (CNXC/MVST/SMPL/BRBR/VRRM):
#   "<subj> (increased|decreased) [by] $X (million|billion), or Y%, … (due to|driven by|…) <cause>"
# The CORE anchor is the "$X …, or Y%" magnitude; a row is emitted ONLY when a causal conjunction
# follows within the window — so a bare "$X, or Y%" table figure with no attribution is NOT a row.
_ATTR_CORE = re.compile(
    r"(increased|decreased)\s+(?:by\s+)?\$\s*([\d,.]+)\s+(million|billion)\s*,?\s+or\s+([\d.]+)\s?%",
    re.I)
_ATTR_CAUSE = re.compile(
    r"\b(due to|driven by|attributable to|as a result of|caused (?:primarily )?by|reflecting)\b",
    re.I)
# metric normalization — the subject snapped to the sentence start carries leading table-cell noise
# ('4 % 94.9 % $ 1,490 … Commercial Services service revenue'); a keyword map recovers the clean
# metric. 'pro\s*fit' tolerates the normalize_text hyphenation artifact ('operating pro fit', BRBR).
_ATTR_METRIC: tuple[tuple[str, str], ...] = (
    ("cost of revenue", r"cost\s+of\s+revenue"),
    ("cost of sales", r"cost\s+of\s+sales"),
    ("operating expenses", r"operating\s+expenses"),
    ("operating profit", r"operating\s+pro\s*fit"),
    ("gross profit", r"gross\s+pro\s*fit"),
    ("gross margin", r"gross\s+margin"),
    ("selling & marketing expense", r"selling\s+and\s+marketing"),
    ("net income", r"net\s+income"),
    ("net sales", r"net\s+sales"),
    ("revenue", r"revenues?\b"),
)


def _attr_metric(subject: str) -> str:
    """The clean metric from a noisy snapped subject — a keyword map, else a trailing letter-phrase.
    A segment-qualified 'X service revenue' keeps the segment (VRRM's per-segment attribution)."""
    low = subject.lower()
    seg = re.search(r"([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,2})\s+service\s+revenue", subject)
    if seg is not None:
        return f"{' '.join(seg.group(1).split())} service revenue".lower()
    for canonical, pat in _ATTR_METRIC:
        if re.search(pat, low):
            return canonical
    words = re.findall(r"[A-Za-z][A-Za-z&'\-]*", subject)
    return " ".join(words[-4:]).lower() if words else "(unlabeled)"


def _attr_lo(text: str, start: int, *, back: int) -> int:
    """The subject-sentence start ≤``back`` chars before the verb — the last '. ' (else the cap).
    Tighter than a table-wide snap so the verbatim can't reach back into a preceding table."""
    lo = text.rfind(". ", max(0, start - back), start)
    return (lo + 2) if lo != -1 else max(0, start - back)


def _attr_subject(text: str, start: int) -> str:
    """The subject text between the prior sentence boundary and the verb at ``start``."""
    return " ".join(text[_attr_lo(text, start, back=90):start].split())[-70:].strip()


#: MEASURED ON THE LIVE CORPUS, not chosen — all 14 committed names' 10-Q primary documents,
#: 40 attribution rows (2026-08-12). Distance from the causal clause to its own sentence end:
#: p50 138 · p90 285 · MAX 477. Full subject→sentence-end fragment: p50 324 · p90 482 · MAX 633.
#:
#: The previous pair (170 / 340) covered 68% and 78% of those, and cut **16 of the 40 rows
#: mid-word — 40% of the corpus, across four names** (UBER 12, SMPL 2, MVST 1, VRRM 1). Four of
#: the cuts severed a dollar figure, including the one that matters most on UBER: the sentence
#: quantifying the UK model change ended at "…negatively impacted reven", dropping "by $1.1
#: billion" — the number that explains why Mobility revenue grew 1% against bookings up 22%.
#:
#: WIDENING CANNOT REACH INTO A SECOND SENTENCE, which is what makes it safe rather than merely
#: bigger: ``text.find(". ", cause_end)`` returns the FIRST boundary after the cause, so the
#: window only decides whether that boundary is ACCEPTED or replaced by a raw offset cut. A wider
#: window accepts the true sentence end more often; it never extends past it.
_ATTR_SENTENCE_WINDOW = 520   # accept the sentence end this far past the cause (max observed 477)
_ATTR_VERBATIM_CAP = 700      # ceiling on the emitted fragment (max observed 633)


def _clip(frag: str, cap: int, *, incomplete: bool = False) -> str:
    """Cut at a WORD boundary and SAY SO — the invisibility was the defect, not the length.

    A silent mid-word cut reads as the filer's own sentence ending there, so a reader cannot tell a
    complete quote from a severed one; that is what let a truncated verbatim carry a number-free
    clause onto the page while every quote-fidelity guard passed (the quoted text really was in the
    filing — it just was not the whole claim). The ellipsis makes the remaining cases legible
    instead of eliminating them, because no bound drawn from today's corpus can promise tomorrow's
    filings fit inside it.

    ``incomplete`` marks a fragment whose SENTENCE never ended inside the window, which is a second
    and independent way to be cut short: it can be well under ``cap`` and still stop mid-clause.
    Marking only the cap would have left that branch exactly as silent as the bug being fixed —
    caught by the run-on test, not by reading.

    THE WORD TRIM APPLIES TO BOTH BRANCHES (review finding). The first cut trimmed only when the
    CAP bit, so an offset-bounded fragment under the cap kept its partial final token and merely
    gained a marker — `"volume v …"`, which still shows a word the filer never wrote. A cap cut and
    an offset cut are equally arbitrary about where they land, so the final token of either may be
    a word fragment; dropping it unconditionally costs at most one whole word off a quote already
    known to be truncated, and is the only version where the guarantee actually holds.
    """
    frag = frag.strip()
    if len(frag) <= cap and not incomplete:
        return frag
    body = frag[:cap] if len(frag) > cap else frag
    # A fragment with no space at all is a single token — there is no word boundary to retreat to,
    # so it keeps its (marked) self rather than becoming empty.
    body = body[:body.rindex(" ")] if " " in body else body
    return f"{body.rstrip(' ,;:')} …".strip()


def _attr_verbatim(text: str, start: int, cause_end: int) -> str:
    """The real attribution sentence — subject start (tight) THROUGH the sentence carrying the cause
    (whose clause may trail into the next sentence, e.g. MVST's 'This decrease was driven by …'),
    single-spaced, with leading table-cell numerics stripped. Never the table-wide window a generic
    sentence-snap would grab. ``cause_end`` is the absolute end of the matched causal clause."""
    lo = _attr_lo(text, start, back=90)
    end = text.find(". ", cause_end)
    # TWO WAYS TO END, and only one of them is a real sentence. When the boundary is found inside
    # the window the quote is COMPLETE; otherwise this is a raw offset and the fragment is
    # known-truncated however short it is, so it gets marked rather than passed off as the filer's
    # own full stop.
    complete = end != -1 and end < cause_end + _ATTR_SENTENCE_WINDOW
    hi = (end + 1) if complete else min(len(text), cause_end + _ATTR_SENTENCE_WINDOW)
    frag = " ".join(text[lo:hi].split())
    # drop leading table-cell debris: numeric cells, and a short lowercase word-FRAGMENT ('venue',
    # a split 're|venue') that is itself glued in front of more table cells. Repeat until a real
    # (capitalized) subject word or the sentence body remains.
    frag = re.sub(r"^(?:[\d\s.,$%()\-]+|[a-z]{1,7}\s+(?=[\d$(]))+", "", frag)
    return _clip(frag, _ATTR_VERBATIM_CAP, incomplete=not complete)


def results_attribution(text: str, *, source_ref: str) -> list[OperatingDriver]:
    """(PR-B A2) MD&A price/volume/mix attribution rows — each a magnitude ($ + %, direction-signed
    into ``value_num``) bound to its causal clause, verbatim. A magnitude with NO stated cause is
    not attribution (skipped); the empty list is an honest miss the collector flags. Never a
    fabricated cause."""
    src = source_ref
    out: list[OperatingDriver] = []
    seen: set[tuple[str, float, str | None]] = set()
    for m in _ATTR_CORE.finditer(text):
        cm = _ATTR_CAUSE.search(text, m.end(), m.end() + 190)
        # accept a cause only in the SAME or immediately-following sentence (≤1 boundary between)
        # — a magnitude with no stated cause must NOT adopt a `due to` from a later, unrelated
        # sentence (2+ away). '3.0' doesn't count: a boundary is a period-then-space.
        if cm is not None and len(re.findall(r"[.]\s", text[m.end():cm.start()])) > 1:
            cm = None
        if cm is None:  # a magnitude with NO stated cause is not attribution
            continue
        pct = _money(m.group(4))
        if pct is None:
            continue
        signed = -pct if m.group(1).lower() == "decreased" else pct
        metric = _attr_metric(_attr_subject(text, m.start()))
        # the period is stated in the magnitude's OWN sentence — bound the search to it so an
        # adjacent PRIOR sentence's period isn't mis-stamped (which then dedup-collides two rows).
        p_lo = text.rfind(". ", max(0, m.start() - 200), m.start())
        p_lo = p_lo + 2 if p_lo != -1 else max(0, m.start() - 90)
        p_hi = text.find(". ", m.end())
        p_hi = p_hi if p_hi != -1 else min(len(text), m.end() + 90)
        period_m = re.search(
            r"(?:three|six|nine)\s+months\s+ended\s+[A-Z][a-z]+\s+\d{1,2},\s+20\d\d",
            text[p_lo:p_hi])
        period = period_m.group(0) if period_m else None
        # period-in-key: a 10-Q reports the SAME line item for 3-mo AND 6-mo; when both round to the
        # same %, keying on (metric, signed) alone silently drops the second — keep them distinct.
        key = (metric, signed, period)
        if key in seen:
            continue
        seen.add(key)
        out.append(OperatingDriver(
            kind=DriverKind.ATTRIBUTION, metric=metric, period=period,
            value=f"${m.group(2)} {m.group(3).lower()}, or {m.group(4)}%",
            value_num=signed, unit="%",
            verbatim=_attr_verbatim(text, m.start(), cm.end()), source_ref=src, tier="anchored",
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
