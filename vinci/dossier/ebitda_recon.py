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
"""
from __future__ import annotations

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
_AMOUNT = re.compile(r"\$\s?([\d,]+(?:\.\d+)?)\s*(million|billion)\b", re.I)
_OPERATING = "operating income + D&A"
_PRETAX = "pre-tax income − net interest income + D&A (other non-operating items stay inside)"
SOURCE_REF = ("CIQ Financials (Quarterly)→Income Statement 'EBITDA' against EDGAR XBRL "
              "(OperatingIncomeLoss, else pre-tax income less a net interest line, plus D&A)")


def _signed(v: float) -> str:
    """A gap in $M with its sign always shown — "+$221M", "−$331M" — so direction is never read."""
    sign = "+" if v > 0 else "−" if v < 0 else ""
    return f"{sign}${abs(v):,.0f}M"


def _quarter(facts: dict[str, Any], tags: list[str] | tuple[str, ...], q: date, *,
             filed_by: date | None = None) -> tuple[float, str] | None:
    """($M, tag) — the discrete quarter ending ``q`` under the first tag that yields one. With
    ``filed_by``, BOTH legs of a difference are read as filed by that date — a prior year-to-date
    restated later is not the one the reader of that day had (the self-funding leg,
    `mechanical._latest_quarter_ocf`)."""
    for tag in tags:
        everything = [p for p in points_for_tag(facts, tag)
                      if filed_by is None or p.filed <= filed_by]
        pts = [p for p in everything
               if p.period_start is not None and abs((p.period_end - q).days) <= _SAME_END_DAYS]
        three = [p for p in pts if p.period_start is not None
                 and _QUARTER_DAYS[0] <= (p.period_end - p.period_start).days <= _QUARTER_DAYS[1]]
        if three:
            return max(three, key=lambda p: p.filed).value / 1e6, tag
        for p in sorted(pts, key=lambda x: x.filed, reverse=True):
            prior = [x for x in everything if x.period_start == p.period_start
                     and _QUARTER_DAYS[0] <= (p.period_end - x.period_end).days
                     <= _QUARTER_DAYS[1]]
            if prior:
                return (p.value - max(prior, key=lambda x: x.filed).value) / 1e6, tag
    return None


def _filing_ebitda(facts: dict[str, Any], q: date,
                   ) -> tuple[float, str, list[str]] | tuple[None, str, list[str]]:
    """(EBITDA $M, construction, tags) — or (None, why, tags) when the quarter cannot be rebuilt."""
    da = _quarter(facts, CONCEPT_ALIASES["dep_amort"], q)
    if da is None:
        return None, "no quarterly D&A tag for this quarter", []
    op = _quarter(facts, CONCEPT_ALIASES["operating_income"], q)
    if op is not None:
        return op[0] + da[0], _OPERATING, [op[1], da[1]]
    pt = _quarter(facts, CONCEPT_ALIASES["pretax_income"], q)
    ni = _quarter(facts, _NET_INTEREST_INCOME, q)
    if pt is None or ni is None:
        return None, ("no operating income, and no pre-tax income with a net interest line, for "
                      "this quarter"), [da[1]]
    return pt[0] - ni[0] + da[0], _PRETAX, [pt[1], ni[1], da[1]]


def _ciq_quarters(bundle: CiqBundle) -> dict[date, float]:
    """CIQ's quarterly EBITDA by fiscal period end, $M — the series the LTM sums."""
    inc = bundle.sheet("financials", "Income Statement", freq="quarterly")
    by_end = lb._dated(lb._row(inc, "For the Fiscal Period Ending", prefix=True),
                       lb._row(inc, "EBITDA"))
    return {d: v for d, v in by_end.items() if v is not None}


def _matching_sentence(text: str, gap: float) -> str | None:
    """The first sentence stating a dollar amount within `MATCH_TOL` of |gap| AND within one unit of
    the amount's own stated precision, verbatim, or None."""
    want = abs(gap)
    if want <= 0:
        return None
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


def reconcile(bundle: CiqBundle, facts: dict[str, Any] | None, releases: list[ReleaseExtract],
              text_for: Callable[[ReleaseExtract], str | None]) -> EbitdaReconciliation | None:
    """The four quarters of CIQ's LTM against the filings. None when there is no quarterly CIQ
    export or no EDGAR facts — nothing to set side by side, which is a different fact from a
    quarter that could not be rebuilt (stated per quarter)."""
    if facts is None or bundle.workbook("financials", freq="quarterly") is None:
        return None
    try:
        ciq = _ciq_quarters(bundle)
    except CiqUnavailableError:
        return None
    ends = sorted(ciq)[-4:]
    if len(ends) < 4:
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
                if text and (quote := _matching_sentence(text, gap)):
                    source = r.source_ref
                    break
        rows.append(EbitdaReconQuarter(
            period_end=q.isoformat(), ciq_ebitda=round(ciq[q], 3), filing_ebitda=round(filing, 3),
            construction=how, tags=tags, gap=round(gap, 3), different=different,
            matching_amount=quote, matching_source=source))
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
        if r.matching_amount:
            part += f" — its release states a matching amount: “{r.matching_amount}”"
        parts.append(part)
    return (f"CIQ's EBITDA is CIQ's own normalised figure, not the filing's{ltm}; "
            + "; ".join(parts) + f" ({how}){tail}. Every EV/EBITDA on this page divides CIQ's "
            "figure.")
