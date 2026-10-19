"""Net debt from EDGAR XBRL — ONE builder, every balance-sheet line read at ONE date (§5.0 row 27).

WHY ONE. The screen's snapshot (:func:`vinci.edgar.client.compute_fundamental_snapshot`) and the
anchor (:func:`vinci.dossier.anchor._lease_inclusive_net_debt`) each built net debt by hand, from
the same per-leg read: every leg at THAT LEG's latest date. Measured 2026-10-19 over 1,694 universe
names with cached companyfacts (`docs/records/2026-10-19-net-debt-one-builder.md`):

* **A tag that stopped was served for years.** 314 names had a long-term-debt leg older than their
  own balance sheet, 99 of them more than 400 days old and worth ≥0.25x EBITDA. A filer that moved
  its debt to a tag outside the alias list kept its last value under the old one: LUMN read a
  $31.5bn balance from 2021 beside a 2026-06-30 balance sheet that carries $13.2bn; KLIC read 2012
  notes it no longer owes.
* **The two formulas disagreed** by ≥0.25x EBITDA on 121 names, beyond the operating leases that
  separate them on purpose, and on the sign of net debt for 49.

ONE BALANCE-SHEET DATE. ``at`` is the cash instant, the convention the anchor's securities leg
already used. Debt, short-term borrowings, cash and securities are FACE lines of every 10-Q, so each
is read AT ``at`` or not at all: a debt tag absent there is not on that balance sheet, and its older
value is not today's. Lease liabilities are the one exception. Many filers disclose them only in
the annual note (BRBR, TGT), so a lease is read as the filer's own total at ``at``, else each part
at ``at`` or at its own latest within :data:`LEASE_MAX_AGE_DAYS`, and older is read as absent.

HOW THE DEBT LINE IS READ, each rule measured on the corpus:

* **Long-term debt including current maturities** is the larger of the bare ``LongTermDebt`` tag
  and noncurrent + current. The bare tag is complete where a current tag is missing (OC: $899M of
  maturing senior notes under ``SeniorNotesCurrent``); noncurrent + current is complete where a
  filer uses the bare tag for the noncurrent part (ANDE, CIFR). Beside a current tag at the same
  date and no noncurrent tag, the bare tag IS the noncurrent line (AAL), and the two are summed.
* **Short-term borrowings** (commercial paper, revolver draws) sit outside long-term debt. Where the
  filer reports its own current-debt total (``DebtCurrent``), the borrowings are that total less
  the current maturities. Otherwise ONE of the three borrowing tags is read, the largest, because
  they overlap (ANDE tags one $249M balance under two of them). It is not added when it IS the
  current maturities tagged a second time (ATEC, VGNT: equal to the dollar), when the bare tag
  shows it inside long-term debt (UBER: $10,726M noncurrent + $1,997M "short-term borrowings" =
  its $12,723M ``LongTermDebt``), or when the filer's own total debt does (CSIQ,
  :func:`_inside_the_total`). NFLX's $2,484M of current notes are read only here; without
  them its net debt was refused, and with them it lands within 0.2% of CIQ's.
* **A debt-and-finance-lease total** (``LongTermDebtAndCapitalLeaseObligations``) is read where no
  noncurrent or bare long-term debt line is on the balance sheet (LUMN, TGT, BURL), and BEFORE a
  bare current tag, which would otherwise stand in for all the debt (PPC: $0.9M beside $2,861M).
  It already contains finance leases, so they are not added a second time.

TWO NAMED BASES, because the two consumers divide by different things:

* :attr:`Basis.LEVERAGE`: borrowings + finance leases − cash − short-term investments. Under US
  GAAP (ASC 842) an operating lease's cost stays inside operating expense, so EBITDA is post-rent,
  and a ratio over it must leave operating leases out. A finance lease's cost sits below EBITDA
  (depreciation and interest), so it is debt on this basis. The screen's leverage ratios read it.
* :attr:`Basis.EV`: LEVERAGE + operating leases, the CIQ TEV ruler. Every multiple the anchor
  bridges is a CIQ TEV multiple, and CIQ's total debt carries operating leases (PARR: EDGAR + leases
  = CIQ's $949M to the dollar), so the bridge must too (the operator's 2026-07-22 convention).

FAIL LOUD. A debt line absent at ``at`` from a filer that used the standard tags before is
REFUSED, never read as zero: of 195 such names, about 110 still show debt elsewhere (another tag at
that date, or material interest expense; AN pays $180M a year), so zero would invent net cash. The
under-capture witness now judges each unread instrument against what the reading can hold
(:func:`_unread_debt`), and the filer's own total debt is a witness too.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import date
from typing import Any

from vinci.edgar.concepts import (
    CONCEPT_ALIASES,
    ConceptPoint,
    extract_points,
    latest_instant,
    points_for_tag,
)

#: The refusal for a filer with no cash line or no debt tag ever: nothing to read, as opposed to a
#: reading that failed a check.
NO_DEBT_OR_CASH = "no debt/cash"


class Basis(enum.StrEnum):
    """Which net debt — named, because a ratio and a bridge need different ones (module doc)."""

    LEVERAGE = "leverage"  # borrowings + finance leases − cash − short-term investments
    EV = "ev"  # LEVERAGE + operating leases: the CIQ TEV ruler


#: A lease tag older than this, measured back from the balance-sheet date, is read as absent. It
#: covers an annual note disclosure: a fiscal year plus the 10-K's filing lag. Lease legs only;
#: debt and cash are face lines and are read at the balance-sheet date or not at all.
LEASE_MAX_AGE_DAYS = 400

#: The CURRENT securities a CIQ TEV nets beside cash ("Total Cash & ST Investments"), in priority
#: order. ONE tag is read, never a sum: a filer can tag one balance twice (a balance-sheet line and
#: its note), and summing would net it twice. Two tags are deliberately ABSENT, because each holds
#: more than the current balance — the bare parent ``MarketableSecurities`` carries the NONCURRENT
#: part too (ORKA: $857.1M parent = $605.1M current + $252.0M noncurrent, and CIQ nets only the
#: $605.1M), and ``AvailableForSaleSecuritiesDebtSecurities`` is every AFS security including those
#: already inside cash equivalents (NFLX: $9,131.5M against $28.7M of short-term investments).
#: Measured 2026-10-08 on the 26 committed names: each tag below is the one that reproduces CIQ's
#: figure where EDGAR and CIQ share a balance-sheet date (AMZN, GOOGL, ORKA, UBER: the first;
#: NFLX: the second; WLK: the third, its `MarketableSecuritiesCurrent` having stopped in 2016).
_SHORT_TERM_SECURITIES_TAGS: tuple[str, ...] = (
    "MarketableSecuritiesCurrent",
    "ShortTermInvestments",
    "AvailableForSaleSecuritiesDebtSecuritiesCurrent",
)

#: Short-term borrowings outside long-term debt. They overlap (a revolver draw can be tagged as
#: both a borrowing and a line of credit), so ONE is read, the largest.
_SHORT_TERM_BORROWING_TAGS: tuple[str, ...] = (
    "ShortTermBorrowings", "CommercialPaper", "LinesOfCreditCurrent",
)

#: Each lease liability as (the filer's total, its current part, its noncurrent part).
_FINANCE_LEASE_TAGS = ("FinanceLeaseLiability",
                       ("FinanceLeaseLiabilityCurrent", "FinanceLeaseLiabilityNoncurrent"))
_OPERATING_LEASE_TAGS = ("OperatingLeaseLiability",
                         ("OperatingLeaseLiabilityCurrent", "OperatingLeaseLiabilityNoncurrent"))

#: The standard debt tags. A filer that reported any of them before, and reports none at the
#: balance-sheet date, has moved its debt somewhere this builder does not read, or repaid it, and
#: the two cannot be told apart here.
_CORE_DEBT_TAGS: tuple[str, ...] = (
    "LongTermDebtNoncurrent", "LongTermDebt", "LongTermDebtCurrent", "DebtCurrent",
    "LongTermDebtAndCapitalLeaseObligations",
    "LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities",
)

# Interest-bearing-debt instrument tags used as a consistency witness (see _unread_debt): an
# instrument the debt line was NOT read from, so one it cannot hold is debt missed. NOT summed
# (tags overlap; summing double-counts).
# Finance-lease tags are excluded (the "is a lease debt" question is genuinely nuanced).
_DEBT_WITNESS_TAGS: tuple[str, ...] = (
    "ShortTermBorrowings", "ConvertibleDebt", "ConvertibleDebtCurrent", "ConvertibleDebtNoncurrent",
    "NotesPayableCurrent", "NotesPayable", "LongTermNotesPayable", "SubordinatedDebtCurrent",
    "SubordinatedDebt", "SecuredDebt", "SecuredDebtCurrent", "LinesOfCreditCurrent",
    "LongTermLineOfCredit", "OtherLongTermDebt", "OtherLongTermDebtNoncurrent",
    "OtherLongTermDebtCurrent",
)

#: The filer's own total of long- and short-term debt. An ARBITER (`_inside_the_total`) and a
#: WITNESS (`_unread_debt`), never the debt line by itself: it can be a note subtotal (MVST).
_FILER_TOTAL_DEBT = "DebtLongtermAndShorttermCombinedAmount"

#: SIC major groups whose balance sheet is the business: banks (60), lenders (61), insurers (63).
#: Their borrowings fund the book they lend or invest, and their cash and securities back deposits
#: and claims, so net debt is not their leverage (capital ratios and debt-to-capital are). Measured
#: 2026-10-19: the builder still produced a "net debt" for 107 of the universe's 279 financials,
#: such as Flagstar at −$10.4bn and Navient at +$44.5bn. The test is by SIC and not by a deposits
#: line, because four non-financials tag ``Deposits`` too (MTN's are season-pass prepayments).
#: Brokers and asset managers (62) and insurance brokers (64) are left in: net debt over EBITDA is
#: how a fee business's leverage is read.
_NOT_APPLICABLE_SIC_GROUPS: frozenset[int] = frozenset({60, 61, 63})


def _at(facts: dict[str, Any], tag: str, at: date) -> ConceptPoint | None:
    """``tag``'s instant value AT ``at`` (the latest filing of it), else None."""
    pts = [p for p in points_for_tag(facts, tag) if p.period_start is None and p.period_end == at]
    return max(pts, key=lambda p: p.filed) if pts else None


def _short_term_securities(facts: dict[str, Any], at: date) -> ConceptPoint | None:
    """The first securities tag in :data:`_SHORT_TERM_SECURITIES_TAGS` reported AT ``at`` — the
    cash instant — else None (a filer without the line nets nothing, like an absent lease tag).

    THE SHARED PERIOD IS THE GUARD (§5.0 row 27). A tag is read only at the cash instant, never at
    its own latest: six of the 26 committed names carry one of these tags that STOPPED before their
    cash instant (EPAM 2024-12-31, LLY 2025-09-30, TGT 2026-01-31, MVST, NKE, ROST), and netting a
    stale balance against today's cash subtracts money the company may no longer hold. CIQ nets
    none of them either. A tag absent at the instant falls through to the next, which is how WLK's
    current figure is found under the third tag."""
    for tag in _SHORT_TERM_SECURITIES_TAGS:
        if (p := _at(facts, tag, at)) is not None:
            return p
    return None


def _same(a: float, b: float) -> bool:
    """One balance tagged twice: equal to within half a percent (in practice, to the dollar)."""
    return abs(a - b) <= 0.005 * max(abs(a), abs(b))


def _lease(facts: dict[str, Any], total: str, parts: tuple[str, str],
           at: date) -> tuple[float, list[ConceptPoint]]:
    """One lease liability: the filer's own total AT ``at`` where it reports one, else each part at
    ``at`` or at its own latest within :data:`LEASE_MAX_AGE_DAYS`. An absent or older part is a
    legitimate 0 (a filer without that lease type).

    THE TOTAL FIRST, because the current part is often a note line that is not on the 10-Q face:
    PENG reports $65.5M of operating leases at 2026-05-29 but only the $59.3M noncurrent part, and
    the total is what reproduces CIQ's figure."""
    if (t := _at(facts, total, at)) is not None:
        return t.value, [t]
    read: list[ConceptPoint] = []
    for tag in parts:
        p = _at(facts, tag, at) or latest_instant(points_for_tag(facts, tag))
        if p is not None and p.period_end <= at and (at - p.period_end).days <= LEASE_MAX_AGE_DAYS:
            read.append(p)
    return sum(p.value for p in read), read


@dataclass(frozen=True)
class Borrowings:
    """The debt line at the balance-sheet date, with every point it was read from."""

    value: float
    read: tuple[ConceptPoint, ...]
    finance_leases_inside: bool  # a debt-and-finance-lease total: leases are not added again
    #: long-term debt including current maturities: the part an unread instrument can sit inside
    long_term: float = 0.0
    #: the filer's own current-debt total where it was read (`DebtCurrent`): it holds every
    #: current instrument, unlike one short-term borrowing line
    current_total: float | None = None


def _unread_debt(facts: dict[str, Any], at: date,
                 b: Borrowings | None) -> tuple[float, str, str] | None:
    """The largest debt balance at or after ``at`` that the debt line read cannot hold, as
    ``(value, tag, what it was held against)`` — the under-capture witness (the MVST case: debt
    under tags the reading does not cover, never a confident false net cash). None when every
    balance is held.

    An instrument the reading was NOT read from is held when it fits inside long-term debt (a
    convertible inside the noncurrent line) or inside the filer's own current-debt total, when it
    IS a balance already read under another tag (ANDE's revolver under two), or when it is the
    whole reading's total (NFLX: `NotesPayable` $14,309M = noncurrent + current notes). One
    short-term borrowing line does NOT hold it: CIQ counts MVST's subordinated and current notes
    beside its bank borrowings, not inside them. The filer's own total debt is held when the
    whole reading reaches it. Values dated before ``at`` are ignored: a since-repaid instrument's
    last value persists at its stale date."""
    us = facts.get("facts", {}).get("us-gaap", {})

    def latest(tag: str) -> float | None:
        pts = [r for r in us.get(tag, {}).get("units", {}).get("USD", [])
               if str(r.get("end", "")) >= at.isoformat() and r.get("val") is not None]
        return (float(max(pts, key=lambda r: (r.get("end", ""), r.get("filed", "")))["val"])
                if pts else None)

    full = b.value if b else 0.0
    hold = max(b.long_term, b.current_total or 0.0) if b else 0.0
    read = {p.tag: p.value for p in b.read} if b else {}
    worst: tuple[float, str, str] | None = None
    for tag in _DEBT_WITNESS_TAGS:
        v = latest(tag)
        if tag in read or v is None or v <= 0:
            continue
        held = (v <= hold * 1.10 or (full > 0 and _close(v, full))
                or any(_same(v, r) for r in read.values()))
        if not held and (worst is None or v > worst[0]):
            worst = (v, tag, f"the ${hold / 1e6:,.0f}M of long-term debt read")
    t = latest(_FILER_TOTAL_DEBT)
    if t is not None and t > full * 1.10 and (worst is None or t > worst[0]):
        worst = (t, _FILER_TOTAL_DEBT, f"the ${full / 1e6:,.0f}M of debt read")
    return worst


def _borrowings(facts: dict[str, Any], at: date) -> Borrowings | None:
    """The debt line AT ``at`` by the rules in the module doc, else None (none on that sheet)."""
    def get(tag: str) -> ConceptPoint | None:
        return _at(facts, tag, at)

    n, tot, ltdc = get("LongTermDebtNoncurrent"), get("LongTermDebt"), get("LongTermDebtCurrent")
    dcur = get("DebtCurrent")
    sb = max((p for t in _SHORT_TERM_BORROWING_TAGS if (p := get(t)) is not None),
             key=lambda p: p.value, default=None)
    read: list[ConceptPoint] = []
    inside = False
    maturities: float | None
    lcl = get("LongTermDebtAndCapitalLeaseObligations")
    lclc = get("LongTermDebtAndCapitalLeaseObligationsCurrent")
    lclt = get("LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities")
    if n is not None or tot is not None:
        if n is None and tot is not None and ltdc is not None:
            # `LongTermDebt` beside a current tag at the SAME date, with no noncurrent tag: it is
            # the noncurrent face line. Where a total settles it (AAL, CMC, CTEV, OIS), 4 of 4.
            long_term, maturities = tot.value + ltdc.value, ltdc.value
        else:
            parts = (n.value if n else 0.0) + (ltdc.value if ltdc else 0.0)
            long_term = max(tot.value, parts) if tot is not None else parts
            # the current maturities INSIDE long-term debt: what the filer's total shows above
            # its noncurrent line, else the current tag
            maturities = long_term - n.value if n is not None else (ltdc.value if ltdc else None)
        read += [p for p in (n, ltdc, tot) if p is not None]
    elif lcl is not None:
        # THE NONCURRENT LINE IS A DEBT-AND-FINANCE-LEASE TOTAL. It is read BEFORE a bare current
        # tag, which would otherwise stand in for all the debt: PPC carries $1M under
        # `LongTermDebtCurrent` beside $2,861M here. The current part is its own tag, else that
        # current tag, else the filer's current-debt total below (CPB).
        cur = lclc or ltdc
        long_term = lcl.value + (cur.value if cur else 0.0)
        maturities = cur.value if cur else 0.0
        read += [p for p in (lcl, cur) if p is not None]
        inside = True
    elif lclt is not None:
        long_term, maturities, dcur, inside = lclt.value, None, None, True
        read.append(lclt)
    elif ltdc is not None:
        long_term = maturities = ltdc.value  # every debt line current
        read.append(ltdc)
    else:
        return None
    dup_of = [v for v in (maturities, ltdc.value if ltdc else None) if v is not None and v > 0]
    current_total = None
    if dcur is not None and maturities is not None:
        # the filer's own current-debt total: borrowings are what it holds beyond the maturities
        short = max(0.0, dcur.value - maturities)
        current_total = dcur.value
        read.append(dcur)
    elif (sb is not None and sb.value > 0 and not any(_same(sb.value, v) for v in dup_of)
          and not _inside_the_total(facts, at, long_term, sb.value)):
        short = sb.value
        read.append(sb)
    else:
        short = 0.0
    return Borrowings(value=long_term + short, read=tuple(read), finance_leases_inside=inside,
                      long_term=long_term, current_total=current_total)


def _inside_the_total(facts: dict[str, Any], at: date, long_term: float, borrowings: float) -> bool:
    """True when the filer's own total debt shows the borrowings already INSIDE long-term debt.

    `DebtLongtermAndShorttermCombinedAmount` is the filer's statement of its long- and short-term
    debt. It ARBITRATES here and is never read as the debt line by itself, because it can be a note
    subtotal: MVST's $118.6M is its bank borrowings only, and CIQ counts $56.9M of subordinated and
    current notes beside it. Where it equals long-term debt alone and not long-term debt plus the
    borrowings, the bare `LongTermDebt` tag already carries them (CSIQ: $6,010.3M both, beside a
    $2,389.0M short-term line that adding would count twice)."""
    total = _at(facts, _FILER_TOTAL_DEBT, at)
    if total is None:
        return False
    return _close(long_term, total.value) and not _close(long_term + borrowings, total.value)


def _close(a: float, b: float) -> bool:
    """Two readings of one total: within 2% (rounding and issuance costs, not a missing line)."""
    return abs(a - b) <= 0.02 * max(abs(a), abs(b))


@dataclass(frozen=True)
class NetDebt:
    """Every net-debt component at ONE balance-sheet date, each with what it was read from.

    ``borrowings`` is None when the debt line could not be read; ``refusal`` then says why, and
    :meth:`value` is None on every basis."""

    at: date
    cash: ConceptPoint
    borrowings: Borrowings | None
    finance_leases: float
    finance_lease_points: tuple[ConceptPoint, ...]
    operating_leases: float
    operating_lease_points: tuple[ConceptPoint, ...]
    securities: ConceptPoint | None
    #: a debt balance the reading cannot hold (`_unread_debt`): (value, tag, held against)
    witness: tuple[float, str, str] | None
    #: a standard debt tag the filer last reported BEFORE ``at`` — set only when none is at ``at``
    stale_debt: ConceptPoint | None

    @property
    def undercaptured(self) -> bool:
        """A debt balance the reading cannot hold exists: debt was missed (`_unread_debt`)."""
        return self.witness is not None

    @property
    def witness_text(self) -> str | None:
        """The debt balance the reading cannot hold, in words, else None."""
        if self.witness is None:
            return None
        v, tag, against = self.witness
        return f"{tag} ${v / 1e6:,.0f}M is more than {against} at {self.at} can hold"

    @property
    def refusal(self) -> str | None:
        """Why net debt is UNKNOWN, else None. :data:`NO_DEBT_OR_CASH` when the filer has never
        tagged a debt line; every other reason is one the depth stage (CIQ) can settle."""
        if self.witness_text is not None:
            return f"EDGAR debt under-captured: {self.witness_text}"
        if self.borrowings is None and self.stale_debt is not None:
            s = self.stale_debt
            if s.period_end > self.at:
                return (f"the cash line was last reported at {self.at}, before the debt line "
                        f"({s.tag} at {s.period_end})")
            return (f"no debt line on the {self.at} balance sheet — {s.tag} last reported "
                    f"${s.value / 1e6:,.0f}M at {s.period_end}; repaid or moved to a tag not read")
        if self.borrowings is None:
            return NO_DEBT_OR_CASH
        return None

    @property
    def debt(self) -> float:
        """The debt line read (0 when none was): for the bridge text and the witness test."""
        return self.borrowings.value if self.borrowings else 0.0

    def value(self, basis: Basis) -> float | None:
        """Net debt ($) on ``basis``, or None when :attr:`refusal` is set."""
        if self.refusal is not None:
            return None
        v = (self.debt + self.finance_leases - self.cash.value
             - (self.securities.value if self.securities else 0.0))
        return v + self.operating_leases if basis is Basis.EV else v

    @property
    def filed(self) -> date:
        """When the latest component read was filed: the figure's knowable date."""
        pts = [self.cash, *(self.borrowings.read if self.borrowings else ()),
               *self.finance_lease_points, *([self.securities] if self.securities else [])]
        return max(p.filed for p in pts)


def net_debt(facts: dict[str, Any]) -> NetDebt | None:
    """Every component at the cash instant, or None when the filer reports no cash line."""
    cash = latest_instant(extract_points(facts, "cash"))
    if cash is None:
        return None
    at = cash.period_end
    b = _borrowings(facts, at)
    stale = None
    if b is None:
        earlier = [p for t in _CORE_DEBT_TAGS
                   if (p := latest_instant(points_for_tag(facts, t))) is not None]
        stale = max(earlier, key=lambda p: (p.period_end, p.filed)) if earlier else None
    fin_pts: list[ConceptPoint] = []
    if b is not None and b.finance_leases_inside:
        fin = 0.0
    else:
        fin, fin_pts = _lease(facts, *_FINANCE_LEASE_TAGS, at)
    opl, opl_pts = _lease(facts, *_OPERATING_LEASE_TAGS, at)
    return NetDebt(
        at=at, cash=cash, borrowings=b, finance_leases=fin, finance_lease_points=tuple(fin_pts),
        operating_leases=opl, operating_lease_points=tuple(opl_pts),
        securities=_short_term_securities(facts, at),
        witness=_unread_debt(facts, at, b), stale_debt=stale,
    )


#: Every tag :func:`net_debt` reads — the fixture builder freezes exactly these, so a test fixture
#: cannot drift from the code (`scripts/build_companyfacts_fixture.py --net-debt-shapes`).
READ_TAGS: frozenset[str] = frozenset({
    *CONCEPT_ALIASES["cash"], *_CORE_DEBT_TAGS, *_SHORT_TERM_BORROWING_TAGS,
    "LongTermDebtAndCapitalLeaseObligationsCurrent",
    *_SHORT_TERM_SECURITIES_TAGS, *_DEBT_WITNESS_TAGS, _FILER_TOTAL_DEBT,
    _FINANCE_LEASE_TAGS[0], *_FINANCE_LEASE_TAGS[1],
    _OPERATING_LEASE_TAGS[0], *_OPERATING_LEASE_TAGS[1],
})


def not_applicable(sic: str | int | None) -> str | None:
    """Why net debt is not a leverage measure for this issuer, else None (see
    :data:`_NOT_APPLICABLE_SIC_GROUPS`)."""
    s = str(sic).strip() if sic is not None else ""
    if not s.isdigit() or int(s) // 100 not in _NOT_APPLICABLE_SIC_GROUPS:
        return None
    return (f"net debt is not a leverage measure for a bank, lender or insurer (SIC {s}): its "
            "borrowings fund the book it lends or invests, and its cash backs deposits and claims")
