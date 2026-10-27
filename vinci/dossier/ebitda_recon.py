"""CIQ's EBITDA IS CIQ's — every quarter of its LTM set against the same quarter rebuilt from XBRL.

WHY (2026-10-21, a review of TJX's page). Every EV/EBITDA on a page divides CIQ's EBITDA, and the
page called that figure "GAAP basis". It is not: CIQ leaves out items it treats as unusual. TJX's
Q2 FY27 reads $1,996M at CIQ and $2,327M rebuilt from the 10-Q (pre-tax $2,018M − net interest
income $31M + D&A $340M) — $331M apart, the gross tariff refund the quarter's release states to the
million; TJX's three earlier quarters agree to the dollar. MEASURED ACROSS THE FLEET the same day,
not a TJX quirk: Target's latest quarter −$956M, Ross's −$253M, Amazon ±$2,500M between two
quarters, Simply Good and Westlake around their impairments — while NFLX, UBER, TECX and VRRM
match. So the page now SAYS which it is, per quarter, and names the construction it compared with.

THE CONSTRUCTION IS STATED, NEVER CHOSEN SILENTLY, and it is the plainest the tags allow:

* operating income + D&A, where the filer tags `OperatingIncomeLoss`; else
* pre-tax income − net interest income + D&A, only where the filer tags a NET interest line whose
  sign is unambiguous (`_NET_INTEREST_INCOME`) — other non-operating items stay inside, and the
  line says so. No net-interest tag → the quarter is not rebuilt, never guessed.

A 10-Q tags D&A (and often operating income) year-to-date; a quarter is the discrete 3-month fact
or, failing that, the year-to-date less the prior quarter's year-to-date from the same start.

WHAT THE RELEASE STATES IS QUOTED, NEVER INFERRED: where a quarter differs, the release filed for it
is searched for a stated dollar amount within :data:`MATCH_TOL` of the gap, and the sentence is
carried verbatim. A match is evidence for the reader to weigh, not an attribution this code makes.

A TABLE STATES AMOUNTS TOO (2026-10-27, VRRM). Verra Mobility's quarter to 2025-12-31 is +$9.352M,
the "Impairment of long-lived assets and right of use assets 9,352" row of the quarter's own
cash-flow table "($ in thousands)" — to the thousand, and in no sentence, so the prose reader quoted
nothing and the gap read as unexplained. Where no sentence matches, a table row's FIRST figure under
the nearest preceding thousands header is read at its own precision, $1K — only where the column
heading proves that first column is the reconciled quarter (`_matching_row`); the quote is that
heading and that row, verbatim, so it re-matches on its own. Shifting every
differing quarter's gap on the corpus by ±3 to ±307 units (544 trials) found one coincidence when
any figure could match — a prior-year column with no label of its own, which a first figure cannot
be — and one with the rule: VITL's $1.359M shifted to $1.382M meets a finance-lease line of 1,381.
Small gaps are where a $1K figure coincides; a table quote is evidence to weigh, as a sentence is.

WAVE 2 (2026-10-27): the 59 quarters still differing unexplained or unchecked, each given its cause.

* THE FOUR COLUMNS MUST BE FOUR QUARTERS. LLY's "Financials_Quarterly" is byte-for-byte its annual
  export (it states 'Period Type: Annual'), so its four "quarters" were four fiscal years set
  against four rebuilt quarters. Columns spanning other than ~273 days are not an LTM: no block.
* D&A ON THE SPLIT PAIR. CNXC tags `Depreciation` and `AmortizationOfIntangibleAssets`, never a
  combined line; the anchor already reads that pair (`anchor._latest_dep_amort`), the quarter now
  does too — the SAME quarter on both legs, or none.
* GROSS INTEREST EXPENSE. BURL stopped tagging a net interest line after its 2025 second quarter
  and tags `InterestExpenseNonoperating` instead; pre-tax income + that expense + D&A is stated as
  its own construction (interest income stays inside with the other non-operating items).
* THE FILING'S OWN TAGGED AMOUNT. A page keeps only the releases among its last ten 8-Ks, so the
  LTM's earlier quarters often have none to search (V, AMZN, WLK). The quarter's own XBRL is
  searched too, for a tagged amount of the kind CIQ leaves out or our construction keeps
  (:data:`_TAGGED_FAMILY`) — matched to $1K, as a table row is. V's three quarters are its
  `LossContingencyLossInPeriod` to the million (903, 708, 329); VITL's its finance-lease
  right-of-use amortization; PARR's the D&A inside its cost of sales; NKE's first its other
  non-operating line. A tag outside the family is never read: TGT's `ContractWithCustomer…
  RevenueRecognized` equals its 115.000 gap exactly and is gift-card revenue, not an EBITDA item.
* CIQ'S OWN ITEMISATION. CIQ's EBITDA is its EBIT plus D&A, and its EBIT leaves out the unusual
  items its quarterly Income Statement lists between 'EBT Excl.' and 'EBT Incl. Unusual Items'.
  Where their net equals the gap (:func:`unusual_explains`), the difference is that normalisation
  by CIQ's own account — a SUM no single stated amount can match: SMPL's $249.0M impairment with
  its restructuring and integration costs, CNXC's goodwill impairments with its merger costs. It
  agrees with every quote already found (TJX, ROST, BRBR, WLK, SMPL to the thousand).
* OFFSETTING QUARTERS. AMZN's quarter to 2025-09-30 is +$2,500M and the next −$2,500M; the LTM
  agrees. Two quarters whose gaps cancel (:func:`_offsets`) state each other: one item, booked in
  another quarter at CIQ — a period mismatch, not a normalisation.
"""
from __future__ import annotations

import json
import re
from collections.abc import Callable
from datetime import date, timedelta
from typing import Any

from vinci.dossier import lease_basis as lb
from vinci.dossier.ciq import CiqBundle, CiqUnavailableError
from vinci.dossier.schemas import EbitdaReconciliation, EbitdaReconQuarter, ReleaseExtract
from vinci.edgar.concepts import CONCEPT_ALIASES, points_for_tag

#: A quarter whose CIQ figure sits this far from the rebuilt one is DIFFERENT. Face validity: the
#: names that match do so to the dollar or within 0.5% (UBER's +$7M on ~$2,000M), so two percent is
#: a gap no rounding or tag choice explains.
DIFFERENT_SHARE = 0.02
#: How close a release's stated amount must sit to the gap to be quoted beside it — AND it must sit
#: within ONE UNIT of its own stated precision ("$707 million" ±1, "$97.0 million" ±0.1). A long
#: release states dozens of amounts, so a share alone finds coincidences: on 2026-10-21 Simply
#: Good's +$95.5M quarter (an $82.0M impairment with integration and restructuring costs) quoted
#: "Selling and marketing expenses of $97.0 million", 1.6% away and fifteen units off its precision.
MATCH_TOL = 0.02
#: A release governs a quarter when it is filed within this many days after the quarter ends.
_RELEASE_WINDOW_DAYS = 80
_SAME_END_DAYS = 7
_QUARTER_DAYS = (80, 100)
_NET_INTEREST_INCOME = ("InterestRevenueExpenseNet", "InterestIncomeExpenseNet",
                        "InterestIncomeExpenseNonoperatingNet")
#: A GROSS interest-expense line — an expense, so its sign is unambiguous; read only where no net
#: line is tagged for the quarter (BURL from its 2025 third quarter).
_INTEREST_EXPENSE = ("InterestExpenseNonoperating", "InterestExpense")
#: D&A on the split pair, where no combined alias reports the quarter (`anchor._latest_dep_amort`).
_SPLIT_DA = ("Depreciation", "AmortizationOfIntangibleAssets")
#: Four quarter-ends span ~273 days (`lease_basis._LTM_SPAN_DAYS`); anything else is not an LTM.
_LTM_SPAN_DAYS = (240, 300)
#: THE TAGGED AMOUNTS A GAP MAY BE QUOTED FROM — us-gaap tag names carrying one of these, the kinds
#: CIQ's EBITDA leaves out (impairments, restructuring, litigation, gains and losses, deal costs)
#: or counts differently (the parts of D&A a filer tags apart). Every other tag is never read: an
#: exact $1M figure in a large filer's facts is common enough to coincide (TGT, 2026-10-27).
_TAGGED_FAMILY = re.compile(r"Impairment|Restructuring|LossContingency|Litigation|GainLoss|"
                            r"BusinessCombination(?:Acquisition|Integration)RelatedCosts|"
                            r"RightOfUseAssetAmortization|CostOfGoodsAndServicesSoldDepreciation")
#: ...and, for the pre-tax construction only, the non-operating line it keeps inside (NKE).
_TAGGED_NONOPERATING = re.compile(r"^OtherNonoperatingIncome")
_AMOUNT = re.compile(r"\$\s?([\d,]+(?:\.\d+)?)\s*(million|billion)\b", re.I)
#: A release table states its scale once, in its header — "($ in thousands)", "(In thousands,
#: except per share data)", "(Dollars in millions)". A header opening with a word must be read
#: too: missed, the rows under it would inherit an earlier thousands header, 1,000x off.
_TABLE_SCALE = re.compile(r"\(\s*(?:\$\s*|[A-Za-z.]+\s+)?in\s+(thousands|millions|billions)\b"
                          r"[^()]{0,60}\)", re.I)
#: A table row as `html_to_text` flattens it: its label, then its FIRST figure — the current
#: period's column. A figure with no label before it is a later column of the row it follows.
_TABLE_ROW = re.compile(r"[A-Za-z][A-Za-z ,'’&/()\-]{0,150}?[A-Za-z)]\s+(?:\$\s*)?\(?\s*"
                        r"(\d{1,3}(?:,\d{3})+)(?![\d,]|\.\d)")
#: A year in a table's column heading — the text between its scale header and its first row.
_HEADING_YEAR = re.compile(r"\b(?:19|20)\d\d\b")
#: The span a table's columns cover, as its heading states it. A QUARTER span opens the heading of
#: the table that can state a quarter's amount; any other span (six or nine months, a year, year to
#: date) means the first column is not the quarter.
_QUARTER_SPAN = re.compile(r"\b(?:three|3)[\s-]+months?\s+ended|\b(?:thirteen|13)[\s-]+weeks?\s+"
                           r"ended|\bquarters?\s+ended", re.I)
_SPAN = re.compile(rf"{_QUARTER_SPAN.pattern}|\b(?:six|nine|twelve|6|9|12)[\s-]+months?\s+ended|"
                   r"\b(?:twenty-six|thirty-nine|fifty-two|fifty-three|26|39|52|53)[\s-]+weeks?\s+"
                   r"ended|\byears?\s+ended|\byear[\s-]+to[\s-]+date", re.I)
#: A table cell — where the rows before a table's title end, so its heading is read from there.
_CELL = re.compile(r"\d{1,3}(?:,\d{3})+")
_OPERATING = "operating income + D&A"
_PRETAX = "pre-tax income − net interest income + D&A (other non-operating items stay inside)"
_PRETAX_GROSS = ("pre-tax income + interest expense + D&A (interest income and other "
                 "non-operating items stay inside)")
SOURCE_REF = ("CIQ Financials (Quarterly)→Income Statement 'EBITDA' against EDGAR XBRL "
              "(OperatingIncomeLoss, else pre-tax income less a net interest line, plus D&A)")


def _signed(v: float) -> str:
    """A gap in $M with its sign always shown — "+$221M", "−$331M" — so direction is never read."""
    sign = "+" if v > 0 else "−" if v < 0 else ""
    return f"{sign}${abs(v):,.0f}M"


def _quarter(facts: dict[str, Any], tags: list[str] | tuple[str, ...], q: date,
             ) -> tuple[float, str] | None:
    """($M, tag) — the discrete quarter ending ``q`` under the first tag that yields one."""
    got = _quarter_cited(facts, tags, q)
    return (got[0], got[1]) if got is not None else None


def _quarter_cited(facts: dict[str, Any], tags: list[str] | tuple[str, ...], q: date,
                   ) -> tuple[float, str, str | None, str | None] | None:
    """($M, tag, form, accession) — `_quarter`, with the filing whose fact ends at ``q`` (a
    derived quarter's later filing, the one that states the longer period)."""
    for tag in tags:
        pts = [p for p in points_for_tag(facts, tag)
               if p.period_start is not None and abs((p.period_end - q).days) <= _SAME_END_DAYS]
        three = [p for p in pts if p.period_start is not None
                 and _QUARTER_DAYS[0] <= (p.period_end - p.period_start).days <= _QUARTER_DAYS[1]]
        if three:
            p = max(three, key=lambda p: p.filed)
            return p.value / 1e6, tag, p.form, p.accession
        everything = points_for_tag(facts, tag)
        for p in sorted(pts, key=lambda x: x.filed, reverse=True):
            prior = [x for x in everything if x.period_start == p.period_start
                     and _QUARTER_DAYS[0] <= (p.period_end - x.period_end).days
                     <= _QUARTER_DAYS[1]]
            if prior:
                return ((p.value - max(prior, key=lambda x: x.filed).value) / 1e6, tag, p.form,
                        p.accession)
    return None


def _dep_amort(facts: dict[str, Any], q: date) -> tuple[float, list[str]] | None:
    """($M, tags) — the quarter's D&A: the first combined alias reporting it, else the split pair
    `Depreciation` + `AmortizationOfIntangibleAssets`, BOTH for this quarter or nothing (one leg
    alone is not the filer's D&A — ORKA and GOOGL's 2025 quarters tag depreciation only)."""
    da = _quarter(facts, CONCEPT_ALIASES["dep_amort"], q)
    if da is not None:
        return da[0], [da[1]]
    legs = [_quarter(facts, [tag], q) for tag in _SPLIT_DA]
    if any(leg is None for leg in legs):
        return None
    return sum(leg[0] for leg in legs if leg is not None), list(_SPLIT_DA)


def _reports_quarter(facts: dict[str, Any], q: date) -> bool:
    """Whether EDGAR carries ANY duration fact ending at ``q`` on the tags the rebuild reads —
    False means the filings, as companyfacts serves them, have not reported the quarter yet."""
    tags = (*CONCEPT_ALIASES["dep_amort"], *_SPLIT_DA, *CONCEPT_ALIASES["operating_income"],
            *CONCEPT_ALIASES["pretax_income"])
    return any(p.period_start is not None and abs((p.period_end - q).days) <= _SAME_END_DAYS
               for tag in tags for p in points_for_tag(facts, tag))


def _filing_ebitda(facts: dict[str, Any], q: date,
                   ) -> tuple[float, str, list[str]] | tuple[None, str, list[str]]:
    """(EBITDA $M, construction, tags) — or (None, why, tags) when the quarter cannot be rebuilt."""
    da = _dep_amort(facts, q)
    if da is None:
        if not _reports_quarter(facts, q):
            return None, ("EDGAR reports nothing for this quarter yet — no D&A, operating-income "
                          "or pre-tax fact ends on it"), []
        return None, ("no quarterly D&A — neither a combined D&A tag nor both of Depreciation and "
                      "AmortizationOfIntangibleAssets for this quarter"), []
    op = _quarter(facts, CONCEPT_ALIASES["operating_income"], q)
    if op is not None:
        return op[0] + da[0], _OPERATING, [op[1], *da[1]]
    pt = _quarter(facts, CONCEPT_ALIASES["pretax_income"], q)
    ni = _quarter(facts, _NET_INTEREST_INCOME, q)
    if pt is not None and ni is not None:
        return pt[0] - ni[0] + da[0], _PRETAX, [pt[1], ni[1], *da[1]]
    ie = _quarter(facts, _INTEREST_EXPENSE, q)
    if pt is not None and ie is not None:
        return pt[0] + ie[0] + da[0], _PRETAX_GROSS, [pt[1], ie[1], *da[1]]
    return None, ("no operating income, and no pre-tax income with a net interest line or an "
                  "interest-expense line, for this quarter"), list(da[1])


def _ciq_quarters(bundle: CiqBundle) -> dict[date, float]:
    """CIQ's quarterly EBITDA by fiscal period end, $M — the series the LTM sums."""
    inc = bundle.sheet("financials", "Income Statement", freq="quarterly")
    by_end = lb._dated(lb._row(inc, "For the Fiscal Period Ending", prefix=True),
                       lb._row(inc, "EBITDA"))
    return {d: v for d, v in by_end.items() if v is not None}


def _ciq_unusual(bundle: CiqBundle) -> dict[date, float]:
    """CIQ's OWN unusual items by fiscal period end, $M — 'EBT Excl. Unusual Items' less 'EBT Incl.
    Unusual Items' on the same quarterly Income Statement: the net of what CIQ itemises and leaves
    out of its EBIT (restructuring, merger costs, impairments, asset writedowns, legal and insurance
    settlements, gains on sale). Empty where the export carries neither row."""
    inc = bundle.sheet("financials", "Income Statement", freq="quarterly")
    head = lb._row(inc, "For the Fiscal Period Ending", prefix=True)
    excl = lb._dated(head, lb._row(inc, "EBT Excl. Unusual Items"))
    incl = lb._dated(head, lb._row(inc, "EBT Incl. Unusual Items"))
    return {d: x - i for d, x in excl.items() if x is not None and (i := incl.get(d)) is not None}


def unusual_explains(gap: float | None, unusual: float | None) -> bool:
    """Whether CIQ's own unusual items for a quarter equal its gap, within `MATCH_TOL` of the gap —
    the difference is then CIQ's normalisation, by its own itemisation (SMPL's quarter to
    2026-02-28: +$258.227M against $258.206M — the $249.0M brand impairment its release states,
    with restructuring and integration costs). ONE definition: the page's line and the
    data-quality scorecard (`vinci.quality.sources.ciq`) both read it. The comparison stays
    independent — the filing's figure is EDGAR's; only the REASON is CIQ's account of itself."""
    if gap is None or unusual is None or gap == 0:
        return False
    return abs(gap - unusual) <= MATCH_TOL * abs(gap)


def _matching_sentence(text: str, gap: float, quarter_end: date | None = None) -> str | None:
    """The first sentence stating a dollar amount within `MATCH_TOL` of |gap| AND within one unit of
    the amount's own stated precision, verbatim — else the first such table row of the quarter
    ending ``quarter_end`` (`_matching_row`) — or None."""
    want = abs(gap)
    if want <= 0:
        return None
    return _matching_prose(text, want) or _matching_row(text, want, quarter_end)


def _matching_prose(text: str, want: float) -> str | None:
    for m in _AMOUNT.finditer(text):
        digits = m.group(1).replace(",", "")
        try:
            v = float(digits)
        except ValueError:
            continue
        scale = 1000.0 if m.group(2).lower() == "billion" else 1.0
        unit = 10.0 ** -len(digits.partition(".")[2]) * scale
        v *= scale
        off = abs(v - want)
        if off <= MATCH_TOL * want and off <= unit + 1e-9:
            lo = max(text.rfind(". ", 0, m.start()) + 2, m.start() - 300, 0)
            hi = text.find(". ", m.end())
            hi = m.end() + 200 if hi == -1 else min(hi + 1, m.end() + 200)
            return " ".join(text[lo:hi].split())
    return None


def _matching_row(text: str, want: float, quarter_end: date | None = None) -> str | None:
    """The first table row whose first figure, under the nearest preceding header, is in thousands
    and sits within `MATCH_TOL` of ``want`` AND within one unit ($1K): the table's heading (its
    span, scale and years) and the row, verbatim, joined by an ellipsis — or None. A row in
    millions, or under no header, has no stated scale here and is never read.

    THE FIRST COLUMN MUST BE THE QUARTER (Codex, #818, two rounds). Its heading — from the last
    table cell before the header to the first row after it — must:
    * name a QUARTER span first (`_QUARTER_SPAN`): VRRM's release carries a three-month cash-flow
      table AND a full-year one, and the year's 114,080 of D&A is no quarter's amount;
    * name a year after the header, the first the latest: nCino heads "Three Months Ended April 30,
      2025 2026", the prior year first, as do 30 of the 258 thousands headers in the committed
      pages' releases;
    * when ``quarter_end`` is given, have that first year be the quarter's.
    Otherwise the period is unproven and the table is not read. The quote carries the heading, so
    it proves the period on its own."""
    heads = list(_TABLE_SCALE.finditer(text))
    # a header is never part of a row's label: masked to the same length, so positions hold
    masked = _TABLE_SCALE.sub(lambda h: "|" * len(h.group(0)), text)
    for m in _TABLE_ROW.finditer(masked):
        head = next((h for h in reversed(heads) if h.end() <= m.start()), None)
        if head is None or head.group(1).lower() != "thousands":
            continue
        off = abs(int(m.group(1).replace(",", "")) / 1000.0 - want)
        if off > MATCH_TOL * want or off > 0.001 + 1e-9:
            continue
        first = _TABLE_ROW.search(masked, head.end())
        end = first.start() if first is not None else head.end()
        years = list(_HEADING_YEAR.finditer(text, head.end(), end))
        if not years or int(years[0].group(0)) != max(int(y.group(0)) for y in years):
            continue
        if quarter_end is not None and int(years[0].group(0)) != quarter_end.year:
            continue
        cells = [c.end() for c in _CELL.finditer(text, max(0, head.start() - 300), head.start())]
        start = cells[-1] if cells else max(0, head.start() - 300)
        spans = list(_SPAN.finditer(text, start, end))
        if not spans or not _QUARTER_SPAN.fullmatch(spans[0].group(0)):
            continue
        lead = " ".join(text[min(spans[0].start(), head.start()):years[-1].end()].split())
        return f"{lead} … {' '.join(text[m.start():m.end()].split())}"
    return None


def _matching_fact(facts: dict[str, Any], gap: float, q: date, construction: str,
                   ) -> tuple[str, str] | None:
    """(quote, source) — the first us-gaap tag in the family (:data:`_TAGGED_FAMILY`, and the
    non-operating line for a pre-tax construction) whose discrete quarter ending ``q`` sits within
    `MATCH_TOL` of |gap| AND within $1K — the precision a table row is read at — or None. The
    quote is the fact as tagged: its name, its amount in dollars and its quarter, so it re-matches
    on its own."""
    want = abs(gap)
    if want <= 0:
        return None
    family = [_TAGGED_FAMILY] + ([_TAGGED_NONOPERATING] if construction != _OPERATING else [])
    for tag in sorted(facts.get("facts", {}).get("us-gaap", {})):
        if not any(f.search(tag) for f in family):
            continue
        got = _quarter_cited(facts, [tag], q)
        if got is None:
            continue
        off = abs(abs(got[0]) - want)
        if off > MATCH_TOL * want or off > 0.001 + 1e-9:
            continue
        form, acc = got[2] or "filing", got[3] or "?"
        return (f"{tag} {got[0] * 1e6:,.0f} USD for the quarter to {q.isoformat()}",
                f"{form} {acc} XBRL")
    return None


def _offsets(rows: list[EbitdaReconQuarter]) -> dict[str, str]:
    """{period_end: the other quarter's} for each pair of DIFFERENT quarters whose gaps cancel —
    opposite signs, the sum within $1M and within `MATCH_TOL` of either gap: one amount CIQ books in
    another quarter than the filings (AMZN, ±$2,500M). A quarter pairs once, oldest first."""
    diff = [r for r in rows if r.different and r.gap is not None]
    out: dict[str, str] = {}
    for i, a in enumerate(diff):
        for b in diff[i + 1:]:
            if a.period_end in out or b.period_end in out:
                continue
            assert a.gap is not None and b.gap is not None
            s = abs(a.gap + b.gap)
            if (a.gap * b.gap < 0 and s <= 1.0
                    and s <= MATCH_TOL * min(abs(a.gap), abs(b.gap))):
                out[a.period_end], out[b.period_end] = b.period_end, a.period_end
    return out


def reconcile(bundle: CiqBundle, facts: dict[str, Any] | None, releases: list[ReleaseExtract],
              text_for: Callable[[ReleaseExtract], str | None]) -> EbitdaReconciliation | None:
    """The four quarters of CIQ's LTM against the filings. None when there is no quarterly CIQ
    export or no EDGAR facts — nothing to set side by side, which is a different fact from a
    quarter that could not be rebuilt (stated per quarter)."""
    if facts is None or bundle.workbook("financials", freq="quarterly") is None:
        return None
    try:
        ciq = _ciq_quarters(bundle)
        unusual = _ciq_unusual(bundle)
    except CiqUnavailableError:
        return None
    ends = sorted(ciq)[-4:]
    if len(ends) < 4:
        return None
    # FOUR QUARTERS OR NO LTM: LLY's quarterly export is its annual one (2026-10-27), and four
    # fiscal years set against four rebuilt quarters would read as four quarters that differ
    if not _LTM_SPAN_DAYS[0] <= (ends[-1] - ends[0]).days <= _LTM_SPAN_DAYS[1]:
        return None
    rows: list[EbitdaReconQuarter] = []
    for q in ends:
        filing, how, tags = _filing_ebitda(facts, q)
        if filing is None:
            rows.append(EbitdaReconQuarter(period_end=q.isoformat(), ciq_ebitda=round(ciq[q], 3),
                                           tags=tags, note=how))
            continue
        gap = ciq[q] - filing
        different = abs(gap) > DIFFERENT_SHARE * abs(filing) and abs(gap) >= 1.0
        quote = source = None
        if different:
            for r in releases:
                if r.filed is None or not q <= r.filed <= q + timedelta(days=_RELEASE_WINDOW_DAYS):
                    continue
                text = text_for(r)
                if text and (quote := _matching_sentence(text, gap, q)):
                    source = r.source_ref
                    break
            if quote is None and (fact := _matching_fact(facts, gap, q, how)) is not None:
                quote, source = fact
        u = unusual.get(q)
        rows.append(EbitdaReconQuarter(
            period_end=q.isoformat(), ciq_ebitda=round(ciq[q], 3), filing_ebitda=round(filing, 3),
            construction=how, tags=tags, gap=round(gap, 3), different=different,
            matching_amount=quote, matching_source=source,
            ciq_unusual=round(u, 3) if u is not None else None))
    # A PAIR THAT CANCELS IS ONE ITEM IN TWO QUARTERS — written on a quarter with no reason of its
    # own, so a quoted or itemised reason is never displaced (that quarter still pairs its mirror)
    offsets = _offsets(rows)
    rows = [r.model_copy(update={"offset_by": offsets[r.period_end]})
            if r.period_end in offsets and not r.matching_amount
            and not unusual_explains(r.gap, r.ciq_unusual) else r for r in rows]
    ciq_ltm = sum(r.ciq_ebitda for r in rows)
    built = [r for r in rows if r.filing_ebitda is not None]
    filing_ltm = sum(r.filing_ebitda or 0.0 for r in built) if len(built) == 4 else None
    ltm_gap = ciq_ltm - filing_ltm if filing_ltm is not None else None
    any_different = any(r.different for r in rows)
    return EbitdaReconciliation(
        quarters=rows, ciq_ltm=round(ciq_ltm, 3),
        filing_ltm=round(filing_ltm, 3) if filing_ltm is not None else None,
        ltm_gap=round(ltm_gap, 3) if ltm_gap is not None else None, any_different=any_different,
        line=_line(rows, ciq_ltm, filing_ltm, ltm_gap), source_ref=SOURCE_REF)


def _line(rows: list[EbitdaReconQuarter], ciq_ltm: float, filing_ltm: float | None,
          ltm_gap: float | None) -> str:
    """The ONE display sentence: which figure the multiples divide, quarter by quarter."""
    built = [r for r in rows if r.filing_ebitda is not None]
    if not built:
        why = sorted({r.note for r in rows if r.note})
        return ("CIQ's quarterly EBITDA could not be set against the filings — "
                + "; ".join(why) + ".")
    hows = sorted({r.construction for r in built if r.construction})
    how = f"rebuilt as {' / '.join(hows)}"
    unbuilt = len(rows) - len(built)
    tail = (f" ({unbuilt} of the four quarters could not be rebuilt)" if unbuilt else "")
    diff = [r for r in built if r.different]
    if not diff:
        return (f"CIQ's EBITDA matches the filings in each quarter set against them ({how}){tail}"
                " — the LTM the multiples divide is the reported figure.")
    # THE LTM AND THE QUARTERS ARE TWO CLAIMS. Amazon's LTM matches the filings to the dollar while
    # two quarters swap $2,500M between them (a charge CIQ books a quarter late); saying the LTM
    # differs there would be false, and saying nothing would hide the quarters.
    if filing_ltm is None or ltm_gap is None:
        ltm = ""
    elif abs(ltm_gap) > DIFFERENT_SHARE * abs(filing_ltm):
        ltm = (f": its LTM ${ciq_ltm:,.0f}M against ${filing_ltm:,.0f}M rebuilt from the filings "
               f"({_signed(ltm_gap)})")
    else:
        ltm = (f": its LTM matches the filings (${ciq_ltm:,.0f}M against ${filing_ltm:,.0f}M), but "
               "not every quarter does")
    parts = []
    for r in diff:
        assert r.filing_ebitda is not None and r.gap is not None
        part = (f"the quarter to {r.period_end}: CIQ ${r.ciq_ebitda:,.0f}M against "
                f"${r.filing_ebitda:,.0f}M ({_signed(r.gap)})")
        if r.matching_amount and (r.matching_source or "").endswith(" XBRL"):
            part += f" — its filing tags a matching amount: {r.matching_amount}"
        elif r.matching_amount:
            part += f" — its release states a matching amount: “{r.matching_amount}”"
        elif unusual_explains(r.gap, r.ciq_unusual):
            part += (f" — CIQ's own export itemises unusual items of ${r.ciq_unusual:,.3f}M for "
                     "the quarter, which it leaves out")
        elif r.offset_by:
            part += (f" — the quarter to {r.offset_by} differs by the same amount the other way: "
                     "one item, in another quarter at CIQ")
        parts.append(part)
    return (f"CIQ's EBITDA is CIQ's own normalised figure, not the filing's{ltm}; "
            + "; ".join(parts) + f" ({how}){tail}. Every EV/EBITDA on this page divides CIQ's "
            "figure.")


# --- the back-fill (2026-10-27): wave 2's reasons onto committed pages, behind a reproduction -----

#: What a committed quarter that WAS rebuilt must carry again, exactly — the figures and how they
#: were built. Its reasons may be added (never changed), and the new keys may appear.
_REPRODUCED = ("ciq_ebitda", "filing_ebitda", "construction", "tags", "gap", "different")


def _unreproduced(held: dict[str, Any], new: dict[str, Any]) -> str | None:
    """The first way ``new`` fails to reproduce the committed block ``held``, or None. A quarter
    the old code rebuilt keeps every :data:`_REPRODUCED` value and any quote it had; a quarter it
    could not rebuild may now be rebuilt (the split pair, the gross interest line) or say better
    why not. The LTM CIQ figure is CIQ's own and never moves."""
    ends = [q.get("period_end") for q in held.get("quarters") or []]
    if ends != [q.get("period_end") for q in new.get("quarters") or []]:
        return f"the quarters are {ends}, the rebuild's another set"
    if held.get("ciq_ltm") != new.get("ciq_ltm"):
        return "CIQ's LTM figure"
    for h, n in zip(held["quarters"], new["quarters"], strict=True):
        if h.get("filing_ebitda") is None:
            if h.get("ciq_ebitda") != n.get("ciq_ebitda"):
                return f"the quarter to {h['period_end']}: ciq_ebitda"
            continue
        for key in _REPRODUCED:
            if h.get(key) != n.get(key):
                return f"the quarter to {h['period_end']}: {key}"
        for key in ("matching_amount", "matching_source"):
            if h.get(key) is not None and h.get(key) != n.get(key):
                return f"the quarter to {h['period_end']}: its committed {key}"
    return None


def backfill_transform(ticker: str, *, facts: dict[str, Any] | None, bundle: CiqBundle | None,
                       text_for: Callable[[ReleaseExtract], str | None],
                       refused: list[str]) -> Callable[[dict[str, Any]], dict[str, Any]]:
    """A `refresh.refresh_dossier` transform rewriting a committed page's
    `financial_summary.ebitda_reconciliation` with wave 2's reasons, under a KEPT synthesis.

    ONLY BEHIND A REPRODUCTION: the quarterly export is the one the page's bands stamp
    (`lease_basis.own_quarterly_export`), and the rebuild from it, EDGAR and the page's own releases
    carries every committed figure again (:func:`_unreproduced`). The one block it REMOVES is one
    whose four columns are not an LTM (LLY's, its annual export under the quarterly name) — proven
    off the committed dates themselves. Anything else is named in ``refused`` and left as it is;
    a page without a block gets none (assembly writes it)."""

    def _apply(mech: dict[str, Any]) -> dict[str, Any]:
        out: dict[str, Any] = json.loads(json.dumps(mech))
        fs = out.get("financial_summary")
        held = fs.get("ebitda_reconciliation") if isinstance(fs, dict) else None
        if not isinstance(fs, dict) or not isinstance(held, dict):
            return out
        if bundle is None or not lb.own_quarterly_export(out, bundle):
            refused.append(f"{ticker}: ebitda_reconciliation — the quarterly export is not the "
                           "page's own")
            return out
        releases = [ReleaseExtract.model_validate(r) for r in
                    ((out.get("primary_source") or {}).get("releases") or [])]
        rec = reconcile(bundle, facts, releases, text_for)
        if rec is None:
            ends = sorted(date.fromisoformat(q["period_end"]) for q in held.get("quarters") or [])
            if len(ends) == 4 and not (_LTM_SPAN_DAYS[0] <= (ends[-1] - ends[0]).days
                                       <= _LTM_SPAN_DAYS[1]):
                fs.pop("ebitda_reconciliation")
            else:
                refused.append(f"{ticker}: ebitda_reconciliation — the rebuild wrote no block")
            return out
        new = json.loads(rec.model_dump_json())
        if (why := _unreproduced(held, new)) is not None:
            refused.append(f"{ticker}: ebitda_reconciliation — the rebuild does not reproduce "
                           f"{why}")
            return out
        fs["ebitda_reconciliation"] = new
        return out

    return _apply
