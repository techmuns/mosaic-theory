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
from typing import NamedTuple

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
_TRANCHE = re.compile(
    r"\b(bond\s+payable|convertible\s+loan|convertible\s+note|term\s+loan|note\s+payable|"
    r"senior\s+notes?|revolving\s+(?:credit\s+)?facility|credit\s+facility)\b[^.]*?"
    r"\$\s*([\d,.]+)\s*(million|billion)[^.]*?matures\s+in\s+([A-Za-z]+\s+20\d\d)",
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

# THE WAYS A 10-Q STATES ITS ≤12m FIGURE (audit E2-D15). Werner's 10-Q says its Credit Facilities
# carry "no principal amount expected to be paid within 12 months" and Netflix's that "the amount of
# principal and interest on our outstanding notes due in the next twelve months is $3,194 million";
# both pages printed "no near-term wall stated in filing". The scale is CAPTURED: "$1.2 billion due
# within the next 12 months" is 1,200, never 1.2. `_DUE_12M` also covers the original "$X million
# due within the next 12 months", which used to be tried first with no debt or lease filter at all —
# so a lease's payments were read as the wall (RE2-D13). Every form now passes `_whole_debt`.
_DUE_12M = re.compile(
    r"\$\s*([\d,.]+)\s*(million|billion)\s+(?:(?:is|are|will\s+be)\s+)?due\s+"
    r"(?:(?:within|in)\s+(?:the\s+next\s+)?(?:12|twelve)\s+months|within\s+one\s+year)\b", re.I)
#: NOT A FORM: "$X of our borrowings were due within the next 12 months" (review round 1 of #1039,
#: 2026-11-12). Microvast's Q3 10-Q (0001628280-26-072316) says "our bank borrowings were $135.3
#: million, our bonds payable were $41.7 million and $120.8 million of our borrowings were due
#: within the next 12 months" — and its $120.8M is the balance sheet's "Short-term bank borrowings
#: 120,794" alone, beside current notes payable (33,470) and bonds payable (41,693) the filing
#: totals at "$ 196.0 million". "Of our borrowings" names no whole, so it is read by no form.
#: A stated ZERO — a KNOWN $0 wall, not an unstated one.
_NO_PRINCIPAL_12M = re.compile(
    r"\bno\s+principal\s+(?:amounts?\s+|payments?\s+)?(?:(?:is|are)\s+)?"
    r"(?:(?:expected|scheduled|required)\s+to\s+be\s+)?(?:paid|payable|due|repaid)\s+"
    r"(?:within|in)\s+(?:the\s+next\s+)?(?:12|twelve)\s+months\b", re.I)
#: PRINCIPAL AND INTEREST in one figure — a different basis from the panel's principal, so it is
#: stored with its basis and never compared with principal as if it were one (`MaturityWall.basis`).
_P_AND_I_12M = re.compile(
    r"\bprincipal\s+and\s+interest\s+on\s+(?:our\s+)?(?:outstanding\s+)?(?:senior\s+)?"
    r"(?:notes|debt|borrowings)\b[^.]{0,60}?\bdue\s+(?:within|in)\s+the\s+next\s+(?:12|twelve)\s+"
    r"months\s+(?:is|was|totals?|totaled)\s+\$\s*([\d,.]+)\s*(million|billion)", re.I)
#: A ≤12m amount in a sentence about leases, purchase obligations or commitments is not the debt
#: wall — Werner states its finance-lease and interest payments "payable within 12 months" too.
_NOT_DEBT = re.compile(r"\bleases?\b|\blease\s+liabilit|purchase\s+obligations?|"
                       r"(?:purchase|capital|inventory)\s+commitments?", re.I)
#: The debt words a ≤12m sentence must carry — `_DEBT_SECTION` plus the plain ones it lacks
#: ("Of our total debt, $1.2 billion due within …", "our notes", "the Credit Facilities").
_DEBT_WORD = re.compile(rf"{_DEBT_SECTION.pattern}|\bdebt\b|\bnotes?\b|\bprincipal\b|"
                        r"credit\s+facilities", re.I)

# PART OF THE DEBT IS NOT THE WALL (TeamNostra fix request 2, V2-N1). #860's widened forms read "Of
# the term loan, $45.0 million is due within one year" as the company's whole ≤12m figure beside
# $500M of notes, and the coherence check AGREED with a CIQ panel that lacked the notes too.
# Helmerich & Payne's 10-Q (0000046765-26-000042) has the shape: "Our indebtedness under our secured
# term loan credit agreements totaled $77.7 million …, of which $6.9 million is due within one
# year", after $1.8bn of senior notes it does not cover. So the clause BEFORE the figure decides:
#: a debt instrument named there makes the figure that instrument's ("under the Credit Facilities",
#: "Of the term loan", "our 2027 Notes") …
_INSTRUMENT = re.compile(
    r"\bterm\s+loans?\b|\brevolv\w*|\bcredit\s+(?:facilit(?:y|ies)|agreements?|lines?)\b|"
    r"\b(?:senior|convertible|exchangeable|secured|unsecured)\s+(?:\w+\s+)?notes\b|"
    r"\d(?:\.\d+)?\s?%\s+(?:\w+\s+){0,2}notes\b|\bnotes\s+due\s+20\d\d\b|\b20\d\d\s+notes\b|"
    r"\b(?:bonds?|notes?)\s+payable\b|\bdebentures\b|\bcommercial\s+paper\b|\bsecuritization\b|"
    r"\b(?:receivables|loan\s+security)\s+(?:\w+\s+)?(?:facilit\w+|agreements?)\b|"
    r"\b(?:the|this|that)\s+(?:loan|notes)\b|\bfacilit(?:y|ies)\b|\bmortgages?\b|"
    # "Term A loan", "Term B-1 Loans"; and debt QUALIFIED by what it is under ("borrowings under
    # the ABL facility", "notes issued pursuant to the indenture") is that instrument's
    r"\bterm\s+[a-z](?:-\d)?\s+loans?\b|\b(?:under|pursuant\s+to)\s+(?:the|our|its|this|that|such)\b",
    re.I)
#: … and with none named, the clause must name the debt in aggregate ("Of our total debt", "the
#: Company had outstanding borrowings of $118.6 million, with", "on our outstanding notes").
_AGGREGATE = re.compile(r"\b(?:debt|indebtedness|borrowings|notes|obligations)\b", re.I)
#: The company's TOTAL debt, stated unqualified — "increasing our outstanding debt to $793.0
#: million" (Werner). One instrument covers the wall when its own principal is this figure; a total
#: followed by "under its Revolving Credit Facility" (Bellring) is that facility's, not a total.
_TOTAL_DEBT = re.compile(
    r"\b(?:outstanding|total)\s+(?:debt|indebtedness|borrowings)\s+(?:to|of|was|were|is|are|"
    r"totaled|totaling|of\s+approximately)\s+\$\s*([\d,.]+)\s*(million|billion)\b"
    # to the clause's end — a decimal point ("$250.0 million under") does not end it
    r"(?!(?:[^.;]|\.(?=\d)){0,80}?\b(?:under|related\s+to|pursuant\s+to|in\s+connection\s+with)\b)",
    re.I)
_FIGURE_M = re.compile(r"\$\s*([\d,.]+)\s*(million|billion)\b", re.I)
BASIS_PRINCIPAL = "principal"
BASIS_PRINCIPAL_AND_INTEREST = "principal and interest"


def _in_millions(num: str, scale: str) -> float | None:
    v = _money(num)
    return None if v is None else v * (1000.0 if scale.lower() == "billion" else 1.0)


#: A sentence end — never the period of an initial or a corporate abbreviation ("Bank of America,
#: N.A. and other lenders", "our U.S. term loan", "Acme Corp. "), which would cut the clause after
#: the instrument it names and leave only an aggregate word ("borrowings") behind it.
_CLAUSE_END = re.compile(r"(?<!\b[A-Z])(?<!\bInc)(?<!\bCorp)(?<!\bCo)(?<!\bLtd)(?<!\bNo)\. ")


def _clause_start(text: str, pos: int, *, cap: int = 400) -> int:
    """Where the sentence holding ``pos`` starts — its words before ``pos`` are the subject a ≤12m
    figure is stated for."""
    lo = max(0, pos - cap)
    ends = list(_CLAUSE_END.finditer(text, lo, pos))
    return ends[-1].end() if ends else lo


def _whole_debt(text: str, lo: int, hi: int, *, stated: float | None, basis: str) -> bool:
    """Is a ≤12m figure whose sentence opens with ``text[lo:hi]`` the COMPANY's, not one
    instrument's?

    With no instrument named, the clause must name the debt in aggregate. With one named, its own
    principal (the clause's last figure) must be the total debt the filing states unqualified
    ELSEWHERE — a total inside the clause itself ("total debt was $500.0 million, and of the term
    loan, …") is its last figure only because the instrument's own principal is unstated.
    ``stated`` and ``basis`` are the ≤12m figure's own, which the balance-sheet route checks."""
    clause = text[lo:hi]
    if not _INSTRUMENT.search(clause):
        return bool(_AGGREGATE.search(clause))
    figs = list(_FIGURE_M.finditer(clause))
    own = [_in_millions(m[1], m[2]) for m in figs]
    if not own or own[-1] is None:
        return False
    # The clause's last figure is the instrument's principal, never a total stated inside the
    # clause ("our total debt was $500.0 million, and of the term loan, $45.0 million …"): checked
    # BEFORE either route, since a filing that repeats its total elsewhere would otherwise let the
    # prose route match the in-clause total to it (review of round 1).
    totals = list(_TOTAL_DEBT.finditer(text))
    last = lo + figs[-1].start(1)
    if any(t.start(1) == last for t in totals if lo <= t.start() < hi):
        return False
    # AT ONE DATE (Codex P1, round 1): a total stated for an earlier balance date — "total debt was
    # $300.0 million at December 31, 2025" beside a June 2026 revolver of $300.0M — covers nothing.
    # The two sentences must share a date, or both state none.
    when = _dates_stated(_sentence(text, hi))

    def same_date(at: int) -> bool:
        dated = _dates_stated(_sentence(text, at))
        return bool(dated & when) if (dated or when) else True

    if any(_in_millions(t[1], t[2]) == own[-1] and same_date(t.start())
           for t in totals if not lo <= t.start() < hi):
        return True
    # ...OR THE BALANCE SHEET'S debt total at the same date (2026-11-12, #956's regression on
    # Werner's Q3, 0000793074-26-000172): its prose total is qualified ("increasing our outstanding
    # debt under our Credit Facilities to $803.0 million"), but its balance sheet carries no debt
    # but "Long-term debt, net of current portion 803,000", so the Credit Facilities are the whole.
    # Review round 1 (A, on #1039): the route holds what the prose route holds, and what a whole
    # debt implies — each a constructed shape round 0 read as a located wall:
    #  * the clause's last figure is the instrument's principal, never a total stated inside the
    #    clause ("our total debt was $500.0 million, and of the term loan, $45.0 million …" beside a
    #    $500.0M balance sheet read located $45.0) — checked above, before both routes;
    #  * the statement states the sheet's date — an undated one covers nothing, as an undated
    #    statement is covered by no dated prose total;
    #  * the figure IS the sheet's current portion, principal to principal: a whole debt's ≤12m
    #    principal is its current portion ("no principal amounts are due" of an undrawn $500.0M
    #    revolver, beside a sheet whose $500.0M is all current, read located $0.0).
    if basis != BASIS_PRINCIPAL or stated is None:
        return False
    bs = _balance_sheet_debt(text)
    return (bs is not None and bs.date in when and abs(bs.total - own[-1]) < 0.05
            and abs(bs.current - stated) < 0.05)


#: The condensed balance sheet: its heading, its unit, and its first column's date.
_BS_HEAD = re.compile(r"\bBALANCE\s+SHEETS?\b[^.]{0,80}?\(\s*in\s+(thousands|millions)", re.I)
#: Where its liabilities start — the body read is the liabilities only, so an asset row ("Notes
#: receivable") is never taken for a borrowing. The section's HEADING is its first "liabilities"
#: ("LIABILITIES AND STOCKHOLDERS’ EQUITY", "Liabilities, redeemable non-controlling interests and
#: equity", Microvast's bare "Liabilities"), never a row's: Uber's first "current liabilities" is
#: the row "Accrued and other current liabilities", below its other current rows (round 1).
_BS_LIABILITIES = re.compile(r"\bliabilities\b", re.I)
#: The rows of its debt: long-term debt net of (or before) its current portion, and that portion.
#: The long-term row is never read inside the current-portion row ("Current portion OF long-term
#: debt 10,000"), which a balance sheet lists first (review round 0: it was read as both).
#: A cell keeps its decimal: "802.6" in a millions table is 802.6, never 802 (round 1).
_BS_LONG_TERM = re.compile(r"(?<![Oo]f\s)\bLong-term\s+debt(?:,?\s+(?:net|less|excluding)"
                           r"[^0-9$—]{0,40})?\s+\$?\s*([\d,]+(?:\.\d+)?|—)", re.I)
_BS_CURRENT = re.compile(r"\bCurrent\s+(?:portion|maturities)\s+of\s+long-term\s+debt\s+"
                         r"\$?\s*([\d,]+(?:\.\d+)?|—)", re.I)
#: Every word a borrowing row can carry. Each must sit in one of the two rows above, or the two
#: are not the whole debt and no total is read — whatever the row's label, and however it runs
#: on before its figure ("Revolving credit facility 50,000", "Notes payable, current", a current
#: row combining debt and leases: review round 0), singular or not, under the common labels
#: round 0 lacked ("Note payable, current", "Bond payable", "Mortgage payable", "Financing
#: obligations", "Receivables securitization facility", "Floor plan payable", "Current maturities
#: of long-term obligations", "Bank overdraft", "Credit agreement": round 1). A lease row carries
#: none of them (#956), and a "(Note 4)" cross-reference is no note payable.
_BS_DEBT_WORD = re.compile(
    r"\b(?:debt|borrowings?|(?<!\()notes?|bonds?|debentures?|commercial\s+paper|"
    r"lines?\s+of\s+credit|revolv\w*|credit\s+(?:facilit\w*|agreements?|lines?)|"
    r"facilit(?:y|ies)|loans?|mortgages?|securitization|floor\s*plan|overdrafts?|"
    r"financ\w*\s+(?:obligations?|liabilit\w*)|long-term\s+obligations?)\b", re.I)
#: A current portion the filing SUBTRACTS in its debt note — "Less: current portion of long-term
#: debt ( 2,748 )" (Amazon's Q3 10-Q), "Less: current portion of long-term notes (3) ( 1,996 )"
#: (Alphabet's Q2, whose note puts it "within accrued expenses and other current liabilities").
#: With no current-portion row on the sheet, that portion sits in a row with no debt word, and the
#: long-term row is part of the debt (round 1). The label may run on ("… of long-term debt and
#: finance leases") and the cell may carry its "$" ("$ ( 10,000 )"), never past a figure or a dash.
#: A footnote marker is never the cell: Alphabet's Q3 "… notes (4) ( 1,996 )" read as a $4 portion.
_NOTE_CURRENT = re.compile(
    r"\bLess:?\s+(?:the\s+)?current\s+(?:portion|maturities)\s+of\s+(?:long-term\s+)?"
    r"(?:debt|notes|borrowings)\b[^()$\d—;.]{0,60}?(?:\s*\(\d\))?\s*\$?\s*"
    r"\((?!\d\))\s*([\d,.]+)\s*\)", re.I)


class _BalanceSheetDebt(NamedTuple):
    date: tuple[str, str, str]  # the first column's balance date
    total: float                # long-term debt plus its current portion, $M
    current: float              # the current portion, $M (0.0 when the sheet lists none)


def _balance_sheet_debt(text: str) -> _BalanceSheetDebt | None:
    """The balance sheet's own date, its debt total and its current portion in $M — long-term debt
    plus any current portion, as its first column states them — or None. None when the balance
    sheet carries any other borrowing row its words name, states no long-term debt row, names no
    unit or date, or lists no current portion the filing's debt note subtracts. What it cannot see
    is debt in a row with no debt word that no "Less: current portion …" line names: the read
    covers the borrowing rows its vocabulary names, never more (the record says which half)."""
    h = _BS_HEAD.search(text)
    if h is None:
        return None
    first = _DATE.search(text, h.end(), h.end() + 400)  # the first column's date, by its heading
    liab = _BS_LIABILITIES.search(text, h.end(), h.end() + 6000)
    if first is None or liab is None:
        return None
    end = text.find("Total liabilities", liab.start())
    body = text[liab.start():end if end != -1 else liab.start() + 6000]
    lt, cur = _BS_LONG_TERM.search(body), _BS_CURRENT.search(body)
    if lt is None:
        return None
    rows = [m.span() for m in (lt, cur) if m is not None]
    if any(not any(a <= w.start() < b for a, b in rows) for w in _BS_DEBT_WORD.finditer(body)):
        return None  # a debt word outside the two rows: another borrowing, so not the whole
    if cur is None and any((v := _money(m[1])) is not None and v > 0
                           for m in _NOTE_CURRENT.finditer(text)):
        return None  # a current portion folded into another row: the long-term row is part
    scale = 0.001 if h[1].lower() == "thousands" else 1.0

    def cell(m: re.Match[str] | None) -> float | None:
        if m is None or m[1] == "—":
            return 0.0
        v = _money(m[1])
        return None if v is None else v * scale

    a, b = cell(lt), cell(cur)
    if a is None or b is None:
        return None
    return _BalanceSheetDebt((first[1], first[2], first[3]), a + b, b)


#: A balance date as a 10-Q states one: "June 30, 2026", "September 30 , 2026".
_DATE = re.compile(r"\b(January|February|March|April|May|June|July|August|September|October|"
                   r"November|December)\s+(\d{1,2})\s*,\s*(20\d\d)\b")


def _dates_stated(sentence: str) -> frozenset[tuple[str, str, str]]:
    """Every date the sentence states — the balance dates a debt figure is given at."""
    return frozenset((m[1], m[2], m[3]) for m in _DATE.finditer(sentence))


class _Stated12m(NamedTuple):
    anchor: int
    total: float | None   # $M due within 12 months
    basis: str
    clause_lo: int        # the clause it is stated for: text[clause_lo:clause_hi]
    clause_hi: int


def _statements_12m(text: str) -> list[_Stated12m]:
    """Every debt ≤12m statement, in the forms' order, each with the clause it is stated for."""
    out: list[_Stated12m] = []
    for m in _DUE_12M.finditer(text):
        sent = _sentence(text, m.start())
        if _DEBT_WORD.search(sent) and not _NOT_DEBT.search(sent):
            out.append(_Stated12m(m.start(), _in_millions(m[1], m[2]), BASIS_PRINCIPAL,
                                  _clause_start(text, m.start()), m.start()))
    for m in _NO_PRINCIPAL_12M.finditer(text):
        if not _NOT_DEBT.search(_sentence(text, m.start())):
            out.append(_Stated12m(m.start(), 0.0, BASIS_PRINCIPAL,
                                  _clause_start(text, m.start()), m.start()))
    for m in _P_AND_I_12M.finditer(text):
        out.append(_Stated12m(m.start(), _in_millions(m[1], m[2]), BASIS_PRINCIPAL_AND_INTEREST,
                              _clause_start(text, m.start(1)), m.start(1)))
    return out


def _stated_12m(text: str, statements: list[_Stated12m] | None = None,
                ) -> tuple[int, float | None, str] | None:
    """(anchor, $M due within 12 months, basis) from the first statement for the WHOLE debt."""
    for st in _statements_12m(text) if statements is None else statements:
        if _whole_debt(text, st.clause_lo, st.clause_hi, stated=st.total, basis=st.basis):
            return st.anchor, st.total, st.basis
    return None


def _part_note(text: str, statements: list[_Stated12m]) -> str | None:
    """The note for a filing whose only ≤12m figures are for part of the debt — LOUD, never a
    silent 'not stated': it names the figure and the sentence it was not taken from."""
    for st in statements:
        total = "an amount" if st.total is None else f"${st.total:,.1f}M"
        return (f"no near-term wall stated in filing for the whole debt — {total} due ≤12m is "
                f"stated for part of it only (“{_sentence(text, st.anchor, cap=240)}”); see CIQ "
                "panel")
    return None


def _maturity_wall(text: str, src: str) -> MaturityWall | None:
    statements = _statements_12m(text)
    stated = _stated_12m(text, statements)
    if stated is not None:  # state='located' — a ≤12m-wall statement was found
        anchor, total, basis = stated
        tranches: list[DebtTranche] = []
        for tm in _TRANCHE.finditer(text[max(0, anchor - 200):anchor + 500]):
            amt = _in_millions(tm.group(2), tm.group(3))
            if amt is None:
                continue
            tranches.append(DebtTranche(
                name=" ".join(tm.group(1).split()).lower(), amount=amt,
                maturity=tm.group(4).strip(),
                verbatim=" ".join(tm.group(0).split())[:200], source_ref=src,
            ))
        return MaturityWall(
            within_12m_total=total, tranches=tranches, state="located", note="",
            basis=None if basis == BASIS_PRINCIPAL else basis,  # absent is principal (the schema)
            verbatim=_sentence(text, anchor), source_ref=src,
        )
    part = _part_note(text, statements)
    if part is not None or _DEBT_SECTION.search(text):  # debt present, but NO ≤12m wall stated
        return MaturityWall(
            within_12m_total=None, tranches=[], state="not_stated", note=part or _NOT_STATED_NOTE,
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


#: A column's ROLE, from the words its header uses: a share of revenue, or of receivables.
_ROLE_WORD = re.compile(r"\b(revenues?|sales|receivables?)\b", re.I)


def _roles(words: list[str]) -> list[str]:
    return ["receivable" if w.lower().startswith("receivable") else "revenue" for w in words]


def _table_header(text: str, row_at: int) -> str:
    """A concentration table's header: from its lead-in sentence to the row, other rows removed."""
    lo = text.rfind(". ", max(0, row_at - 1200), row_at)
    lo = lo + 2 if lo != -1 else max(0, row_at - 1200)
    return " ".join(_CUST.sub(" ", text[lo:row_at]).split())


def _column_roles(head: str) -> list[str] | None:
    """The roles of a concentration table's columns, in order, read from its HEADER — or None when
    the header names no role. A row's figures took their roles from POSITION (audit E2-D16): Vital
    Farms' 10-Q follows its revenue table with an accounts-receivable one, and the receivable
    table's "Customer C 11 % 10 %" reached the page as an 11% REVENUE concentration with a 10%
    prior. The header is the text from the lead-in sentence to the table's first row; the column
    headings are the part after its colon, and the lead-in alone decides when they name no role."""
    colon = head.rfind(":")
    cols = _ROLE_WORD.findall(head[colon + 1:]) if colon != -1 else []
    roles = _roles(cols or _ROLE_WORD.findall(head))
    if not roles:
        return None
    return roles if cols else ([roles[0]] if len(set(roles)) == 1 else ["mixed"])


#: Every note `_concentration` writes for a row it refuses starts with this.
CONCENTRATION_REFUSAL_PREFIX = "Concentration row refused"


def _concentration(text: str, src: str,
                   notes: list[str] | None = None) -> CustomerConcentration | None:
    custs: list[ConcentrationCustomer] = []
    seen: set[str] = set()
    refusals: list[str] = notes if notes is not None else []

    def _refuse(row: str, roles: list[str], header: str) -> None:
        # ALOUD (review round 1): a row dropped for its role with no note let a revenue
        # concentration vanish silently — the note names the customer and the header it read
        why = ("the header names both revenue and receivables and no column says which"
               if roles == ["mixed"] else "its first column is a receivable share, not revenue")
        refusals.append(f"{CONCENTRATION_REFUSAL_PREFIX} — {why}: “{' '.join(row.split())}” under "
                        f"“…{header[-160:]}” ({src})")
    # (1) table form — 'Customer A 52 % 31 %' → exact, its columns' roles read from the header
    for m in _CUST.finditer(text):
        name = f"Customer {m.group(1).upper()}"
        pct = _money(m.group(2))
        if name in seen or pct is None or pct > 100:
            continue
        header = _table_header(text, m.start())
        roles = _column_roles(header)
        if roles is not None and roles[0] != "revenue":
            _refuse(m.group(0), roles, header)  # a receivables table, or a lead-in naming both
            continue
        # the second figure is a PRIOR revenue share only when its column is a revenue column too
        # — or when the header names one role for every column ("% of net revenue … 2026 2025")
        second_is_revenue = roles is None or len(roles) == 1 or roles[1] == "revenue"
        seen.add(name)
        custs.append(ConcentrationCustomer(
            name=name, pct=pct,
            prior_pct=_money(m.group(3)) if m.group(3) and second_is_revenue else None,
            value_kind="exact",
        ))
    # (2) prose EXACT — 'The {Named} represented 15.2% and 15.4%' → exact (preferred over floor)
    if not custs:
        for m in _CUST_EXACT.finditer(text):
            pct = _money(m.group(2))
            name = " ".join(m.group(1).split())
            if pct is None or pct > 100 or name in seen:
                continue
            # the roles the sentence names AFTER the figures, in order: "15.2% and 41.0% of
            # revenue and accounts receivable, respectively" makes the second a receivable share
            stop = text.find(". ", m.end())
            tail = text[m.end():stop if stop != -1 else m.end() + 160][:160]
            roles = _roles(_ROLE_WORD.findall(tail))
            if roles and roles[0] != "revenue":
                _refuse(m.group(0), roles, tail)
                continue
            seen.add(name)
            custs.append(ConcentrationCustomer(
                name=name, pct=pct,
                prior_pct=(_money(m.group(3)) if m.group(3)
                           and (len(roles) < 2 or roles[1] == "revenue") else None),
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
    r"\$\s*([\d,.]+)\s*(million|billion)\s+(?:in|of)\s+(purchase|capital)\s+commitments"
    r"(?:\s+with\s+\$\s*([\d,.]+)\s*(million|billion)\s+due\s+within)?",
    re.I,
)


def _commitments(text: str, src: str) -> list[Commitment]:
    out: list[Commitment] = []
    for m in _COMMIT.finditer(text):
        # the scale is captured, as the wall's is (E2-D15): "$2.1 billion of purchase commitments"
        amt = _in_millions(m.group(1), m.group(2))
        if amt is None:
            continue
        out.append(Commitment(
            kind=m.group(3).lower(), amount=amt,
            within_12m=_in_millions(m.group(4), m.group(5)) if m.group(4) else None,
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
    flags: list[str] = []
    conc = _concentration(text, source_ref, flags)
    if wall is None:
        flags.append(f"no anchored pattern matched — maturity wall: {source_ref}")
    if conc is None:
        flags.append(f"no anchored pattern matched — customer concentration: {source_ref}")
    return FilingSectionExtract(
        source_ref=source_ref, going_concern=_going_concern(text, source_ref),
        maturity_wall=wall, concentration=conc, commitments=_commitments(text, source_ref),
        qa_flags=flags,
    )
