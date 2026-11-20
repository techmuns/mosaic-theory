"""WHAT THE HEADLINE EV/EBITDA IS STRUCK ON, and R1's ex-lease multiple at the page's price.

WHY (2026-10-21, a review of TJX's page). The page printed CIQ's TEV/LTM EBITDA, 13.3x, with no
basis, and a reader divided CIQ's TEV ($170,372M) by reported LTM EBITDA ($8,903M) to get 19.1x and
called the headline wrong. Neither is wrong arithmetic; they are different pairings, and only one
is consistent:

    TEV WITH operating leases ÷ EBITDA WITH rent added back      13.4x   (CIQ's, since ASC 842)
    TEV LESS operating leases ÷ reported EBITDA                  17.8x   (R1's, at the page's price)
    TEV WITH leases ÷ reported EBITDA                            19.1x   (neither: a basis mix)

So two figures are built here, both from the page's own fields:

* :func:`headline_basis` MEASURES which pairing CIQ's multiple reproduces on this page: its
  implied denominator (TEV ÷ multiple) against reported LTM EBITDA and against reported EBITDA plus
  rent. Measured, never assumed — on the 2026-10-21 fleet 14 of 23 measurable pages reproduce the
  rent-inclusive pairing, NFLX the reported one, five cannot be told apart (rent under 5% of
  EBITDA) and four reproduce neither, so a fleet-wide label would be wrong a third of the time.
* :func:`ex_lease_at_price` strikes R1's ex-lease basis at the page's stored close. The ex-lease
  history's `current` is the latest QUARTERLY close in CIQ's Historical Capitalization (TJX 16.3x at
  2026-08-28); a reader asked for "today's" multiple on R1's basis had to rebuild it by hand.

ONE DATE OR NO DIVISION (W65, 2026-11-19). TEV ÷ the multiple is the EBITDA the multiple divides
only when both are struck on one price. They are read from two CIQ exports: the TEV from Comparable
Analysis (its data date, `implied_expectations.tev_as_of`) and the multiple from the Multiples
sheet's latest Close (its column's date, the own-history band's `as_of`). GOOGL's page divided its
2026-10-30 TEV ($3,316,548M) by its 2026-09-30 close (22.9x), across a fall from $344.08 to about
$283.72, and called the $144,827M quotient an EBITDA that "reproduces neither pairing". AMZN carries
the same 30 days, and there the quotient landed on reported EBITDA, a rent-free reading on a page
whose rent is material. So :func:`headline_basis` reads the multiple's close first: within
:data:`SAME_PRICE_DAYS` of the TEV's date it measures as before; beyond it, or with either date
unstated or not a date, it STATES both dates and divides nothing.

Every threshold is set by face validity, never by what any name's figure would come to.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from vinci.dossier.schemas import EvEbitdaAtPrice, EvEbitdaBasis, MechanicalLayer, SourceStatus

#: How far the multiple's implied denominator may sit from a pairing and still reproduce it. The
#: rent is ANNUAL (CIQ's last fiscal year) against an LTM EBITDA, the multiple prints at one
#: decimal, and the comps TEV can sit days from the multiple's close — each worth a few percent.
#: Measured 2026-10-21: the 14 pages that reproduce EBITDA + rent do so within 0.7%–4.9%.
PAIRING_TOL = 0.05

#: How many calendar days the comps TEV's date and the multiple's close may sit apart, either way,
#: and still be one price (W65). Face validity, from how the two are dated: CIQ dates the comps TEV
#: at the last close before its export and a Multiples column at the export day, so one export's
#: two figures sit up to a weekend plus a holiday apart (LLY: TEV 2026-10-30, a Friday; its
#: Multiples close 2026-11-02, the Monday). Four days is the longest routine gap between two
#: consecutive trading sessions, the same calendar fact `freshness.MAX_STORE_LAG_DAYS` measures in
#: the price store. Within it, at most four sessions' moves separate the figures, about 4% at a 30%
#: annual volatility, inside PAIRING_TOL's 5%. A month is about 9%: GOOGL's quotient then measures
#: the price's move as much as the basis. Not chosen to catch or spare any name (every limit from 3
#: to 29 days separates the 26 pages of 2026-11-19 alike).
SAME_PRICE_DAYS = 4

#: The readings under which nothing is divided: the two dates differ by more than SAME_PRICE_DAYS,
#: or one of them is not stated. Every other reading is a measured pairing.
DATE_READINGS = frozenset({"dates_differ", "date_unstated"})


def _iso(x: Any) -> str | None:
    """A page date as the ISO string these blocks store — `stock_info.as_of` is a `date`, the comps
    TEV's as-of a string; both are written one way."""
    if x is None:
        return None
    return x.isoformat() if hasattr(x, "isoformat") else str(x)


def _money(v: float) -> str:
    """$M with the sign in front of the symbol: a net-cash bridge reads −$3,133M, never $-3,133M."""
    return f"{'−' if v < 0 else ''}${abs(v):,.0f}M"


#: THE TWO CIQ EBITDAs A PAGE CARRIES, EACH NAMED ONE WAY WHEREVER IT PRINTS (W81, SP-D20; operator
#: 2026-11-19, "Approve with correction"). They are different figures: MORN's annual LTM is 719.4
#: and its four quarters sum to 822.1, the annual leaving out the Cash Flow's 'Other Amortization'.
#:
#: The LTM column of CIQ's ANNUAL export — what `_ltm_ebitda` reads, and what this block's
#: pairings are measured against. It was printed as "reported LTM EBITDA", which reads as the
#: company's filed figure; it sat beyond 2% of the filing-rebuilt EBITDA on 10 of the 17 committed
#: pages carrying both (main 6e03501f, 2026-11-19). The stored key keeps its name
#: (`EvEbitdaBasis.reported_ltm_ebitda`); only the printed words change.
ANNUAL_LTM = "CIQ's annual LTM EBITDA"
#: The QUARTERLY export's EBITDA summed over four quarters: the ex-lease history's denominator
#: (`lease_basis`), the at-price multiple's, and the EBITDA reconciliation's LTM (`ebitda_recon`).
FOUR_QUARTER = "CIQ's four-quarter EBITDA"


def _ltm_ebitda(mech: MechanicalLayer) -> float | None:
    """CIQ's annual LTM EBITDA, $M: the financial summary's structured `LTM` value, never a cell."""
    fs = mech.financial_summary
    if fs is None or fs.annual.status is not SourceStatus.PRESENT or fs.annual.value is None:
        return None
    tbl = fs.annual.value
    if "LTM" not in tbl.columns:
        return None
    i = tbl.columns.index("LTM")
    row = next((r for r in tbl.rows if r.label == "EBITDA ($M)"), None)
    vals = list(row.values or []) if row is not None else []
    v = vals[i] if i < len(vals) else None
    return float(v) if isinstance(v, (int, float)) else None


def multiple_close(mech: MechanicalLayer) -> tuple[str | None, str]:
    """The close CIQ's headline TEV/LTM EBITDA is struck at, as ``(ISO date, "")``, or
    ``(None, why it is not dated)``.

    Read off the own-history EV/EBITDA band: `ciq_sheets._latest_close` selects the band's current
    and `as_of` and `ev_ebitda_current`'s value from one Close row, so they are one cell. The band's
    current must still be the headline multiple (`anchor_split.SAME_MULTIPLE_TOL`, the headline's
    one decimal): a band carrying another multiple does not date this one."""
    from vinci.dossier.anchor_split import SAME_MULTIPLE_TOL

    val = mech.valuation
    mult = val.ev_ebitda.value
    oh = val.own_history
    bands = oh.value if oh is not None and oh.status is SourceStatus.PRESENT and oh.value else []
    band = next((b for b in bands if "EBITDA" in b.metric), None)
    if band is None:
        return None, ("the page carries no own-history EV/EBITDA band, the read that dates CIQ's "
                      "Multiples close")
    if mult is None or abs(band.current - mult) > SAME_MULTIPLE_TOL + 1e-9:
        return None, (f"the own-history band's current ({band.current:g}x) is not the headline "
                      f"multiple ({mult}x), so its date is not this multiple's")
    if not band.as_of:
        return None, "the own-history band's latest close carries no date"
    return band.as_of, ""


def _day(s: str | None) -> date | None:
    """An ISO date, or None when the string is not one: `implied_expectations.tev_as_of` carries
    the placeholder "UNKNOWN" when the comps date could not be corrected (`mechanical`)."""
    try:
        return date.fromisoformat(s[:10]) if s else None
    except ValueError:
        return None


def days_apart(tev_as_of: str | None, close: str | None) -> int | None:
    """The comps TEV's date less the multiple's close, in calendar days; None when either is
    unstated or not a date (never a raise: an undated pair is stated, not a failed build)."""
    t, c = _day(tev_as_of), _day(close)
    return (t - c).days if t is not None and c is not None else None


def _not_one_date(mech: MechanicalLayer, mult: float, tev: float, ltm: float,
                  close: str | None, why: str, gap: int | None) -> EvEbitdaBasis:
    """The block when the TEV and the multiple are not shown to be of one date: both dates stated,
    the reported figures kept, and NO quotient, ratio or pairing (W65). A quotient of two dates'
    figures folds the price's move between them into "EBITDA" (GOOGL's $144,827M)."""
    ie = mech.valuation.implied_expectations
    assert ie is not None                                 # the caller read its TEV
    lb = mech.valuation.lease_basis
    rent = lb.rent_expense if lb is not None and lb.rent_expense and lb.rent_expense > 0 else None
    tev_day = _iso(ie.tev_as_of)
    if gap is not None:
        assert close is not None
        reading = "dates_differ"
        when = (f"{gap} days later" if gap > 0 else f"{-gap} days earlier")
        line = (f"CIQ's {mult:.1f}x is struck at the {close} close and the comps TEV "
                f"(${tev:,.0f}M) at {tev_day}, {when}: more than the {SAME_PRICE_DAYS} days within "
                "which the two are one price. TEV ÷ the multiple would read the price's move "
                "between the two dates as EBITDA, so which EBITDA the multiple divides is not "
                "measured. It is measured again when the Multiples sheet's latest close sits "
                f"within {SAME_PRICE_DAYS} days of the comps TEV's date.")
    else:
        # an undated multiple (`why` says what the page lacks), or a comps TEV whose date is not
        # one (`tev_as_of` reads "UNKNOWN" when the comps date could not be corrected)
        reading = "date_unstated"
        if why:
            what, tev_when = why, tev_day or "date unstated"
        else:
            what, tev_when = f"the comps TEV's date reads {tev_day!r}, not a date", "undated"
        line = (f"CIQ's {mult:.1f}x and the comps TEV (${tev:,.0f}M, {tev_when}) are not shown "
                f"to be of one date ({what}), so which EBITDA the multiple divides is not "
                "measured.")
    return EvEbitdaBasis(
        multiple=mult, tev=round(tev, 3), tev_as_of=tev_day,
        implied_denominator=None, reported_ltm_ebitda=round(ltm, 3),
        rent=rent, rent_fiscal_year=lb.rent_fiscal_year if lb is not None else None,
        ratio_to_reported=None, ratio_to_reported_plus_rent=None,
        reading=reading, tolerance=PAIRING_TOL, line=line,
        multiple_close=close, days_apart=gap, days_apart_tolerance=SAME_PRICE_DAYS,
        source_ref=("Assembler: the EBITDA a CIQ TEV/LTM EBITDA multiple divides — not measured: "
                    f"the comps TEV ({tev_day or 'date unstated'}) and the Multiples close "
                    f"({close or 'date unstated'}) are not within {SAME_PRICE_DAYS} days"))


def headline_basis(mech: MechanicalLayer) -> EvEbitdaBasis | None:
    """CIQ's headline TEV/LTM EBITDA, read against the two consistent-or-not pairings, or None when
    the page lacks a positive multiple, a snapshot TEV or a positive reported LTM EBITDA.

    The pairing is measured only when the TEV and the multiple are of one date, within
    :data:`SAME_PRICE_DAYS` (W65). Otherwise the block states both dates and divides nothing."""
    val = mech.valuation
    ev = val.ev_ebitda
    ie = val.implied_expectations
    if ev.status is not SourceStatus.PRESENT or not ev.value or ev.value <= 0 or ie is None:
        return None
    if ie.tev.status is not SourceStatus.PRESENT or not ie.tev.value or ie.tev.value <= 0:
        return None
    ltm = _ltm_ebitda(mech)
    if ltm is None or ltm <= 0:
        return None
    tev, mult = float(ie.tev.value), float(ev.value)
    close, why = multiple_close(mech)
    gap = days_apart(_iso(ie.tev_as_of), close)
    if gap is None or abs(gap) > SAME_PRICE_DAYS:
        return _not_one_date(mech, mult, tev, ltm, close, why, gap)
    lb = val.lease_basis
    rent = lb.rent_expense if lb is not None and lb.rent_expense and lb.rent_expense > 0 else None
    implied = tev / mult
    r_rep = implied / ltm
    r_rent = implied / (ltm + rent) if rent is not None else None
    ok_rep = abs(r_rep - 1) <= PAIRING_TOL
    ok_rent = r_rent is not None and abs(r_rent - 1) <= PAIRING_TOL
    fy = lb.rent_fiscal_year if lb is not None else None
    tev_day = _iso(ie.tev_as_of) or "date unstated"
    head = f"CIQ's {mult:.1f}x divides TEV ${tev:,.0f}M (comps, {tev_day}) by ${implied:,.0f}M"
    rent_txt = (f"{ANNUAL_LTM} ${ltm:,.0f}M + rent ${rent:,.0f}M"
                f"{f' (FY ending {fy})' if fy else ''} = ${ltm + rent:,.0f}M" if rent is not None
                else "")
    if ok_rep and ok_rent:
        assert rent is not None                          # `ok_rent` needs a measured rent
        reading = "indistinguishable"
        line = (f"{head}, which reproduces {ANNUAL_LTM} (${ltm:,.0f}M) and that plus rent "
                f"alike — rent is {rent / ltm:.1%} of EBITDA, too small for the pairing to change "
                "the reading.")
    elif ok_rent:
        assert r_rent is not None and rent is not None
        reading = "ebitda_plus_rent"
        line = (f"{head}: {rent_txt} ({abs(r_rent - 1):.1%} apart) — TEV WITH the operating "
                f"leases over EBITDA WITH rent added back, consistent on its own basis. It is NOT "
                f"a multiple of {ANNUAL_LTM}, after rent (${ltm:,.0f}M, {1 - 1 / r_rep:.1%} below "
                "the denominator).")
    elif ok_rep:
        reading = "reported"
        line = (f"{head}: {ANNUAL_LTM} ${ltm:,.0f}M ({abs(r_rep - 1):.1%} apart) — a "
                "multiple of that figure, after rent.")
    else:
        reading = "not_reproduced"
        alt = (f" and {rent_txt} ({r_rent - 1:+.1%})" if rent is not None and r_rent is not None
               else "")
        line = (f"{head}, which reproduces neither pairing: {ANNUAL_LTM} ${ltm:,.0f}M "
                f"({r_rep - 1:+.1%}){alt}. Read CIQ's own denominator before comparing it with a "
                "multiple struck after rent.")
    return EvEbitdaBasis(
        multiple=mult, tev=round(tev, 3), tev_as_of=_iso(ie.tev_as_of),
        implied_denominator=round(implied, 3), reported_ltm_ebitda=round(ltm, 3),
        rent=rent, rent_fiscal_year=fy, ratio_to_reported=round(r_rep, 6),
        ratio_to_reported_plus_rent=round(r_rent, 6) if r_rent is not None else None,
        reading=reading, tolerance=PAIRING_TOL, line=line,
        multiple_close=close, days_apart=gap, days_apart_tolerance=SAME_PRICE_DAYS,
        source_ref=("Assembler: the EBITDA a CIQ TEV/LTM EBITDA multiple divides — CIQ comps TEV ÷ "
                    "the multiple, against reported LTM EBITDA and rent"
                    + (f" (TEV as of {_iso(ie.tev_as_of)})" if _iso(ie.tev_as_of) else "")))


def at_price_line(*, price: float, price_as_of: str | None, shares: float, shares_basis: str,
                  net_debt: float, ltm_ebitda: float, ltm_through: str, value: float) -> str:
    """The at-price block's sentence, from its own stored fields — ONE writer, so the panel's
    transform (`vinci.evals.variants.w81_ebitda_names`) re-reads it exactly as the builder writes
    it (W81: the denominator is CIQ's four-quarter EBITDA)."""
    return (f"at the page's ${price:,.2f} close ({price_as_of or 'date unstated'}): "
            f"(${price:,.2f} × {shares:,.0f} {shares_basis} + net debt {_money(net_debt)} "
            f"excluding operating leases) ÷ {FOUR_QUARTER} ${ltm_ebitda:,.0f}M (to "
            f"{ltm_through}) = {value:.1f}x")


def ex_lease_at_price(mech: MechanicalLayer, facts: dict[str, Any] | None,
                      ) -> EvEbitdaAtPrice | None:
    """R1's ex-lease EV/EBITDA at the page's stored close — only where R1 prices that basis (rent
    material and an ex-lease history built), and only from a complete bridge: a price, the
    anchor's share count (`share_denominator` — the one its base value divides), net debt excluding
    operating leases (the anchor's builder) and the history's latest LTM EBITDA. None otherwise,
    never a partial figure.

    ONE CUT FOR THE WHOLE BRIDGE (2026-11-03, after #885). ``facts`` are cut ONCE, at the stored
    close's date — `vinci.edgar.asof.page_price_date`'s answer whenever there is a close; a close
    with no date strikes nothing, before any fact is read — so the share count and net debt read
    the same filings.
    #885 cut net debt only, and the valuation-bases refresh hands this the UNCUT blob: NCNO's
    multiple paired its 2026-08-17 balance sheet with the diluted average of a 10-Q filed
    2026-08-25 (29.4x; 30.5x as filed by its price date)."""
    # the anchor's ONE bridge builder and ONE denominator
    from vinci.dossier.anchor import _lease_inclusive_net_debt, share_denominator
    from vinci.edgar.concepts import facts_as_of

    lb = mech.valuation.lease_basis
    si = mech.stock_info
    if lb is None or not lb.material or lb.ex_lease_band is None or si is None or not facts:
        return None
    last = next((o for o in reversed(lb.observations) if o.multiple is not None), None)
    if last is None or last.ltm_ebitda <= 0:
        return None
    price = si.price.value if si.price.status is SourceStatus.PRESENT else None
    if not price or si.as_of is None:   # no dated close: nothing to strike at, no cut to read at
        return None
    facts = facts_as_of(facts, si.as_of)   # E2-D21: every leg below reads this one cut
    count = share_denominator(mech.model_dump(mode="json"), facts)
    nd = _lease_inclusive_net_debt(facts, as_of=None, ex_operating_leases=True)
    if count is None or nd is None or nd[0] is None:
        return None
    shares, shares_basis = count
    nd_m = nd[0] / 1e6
    ev = price * shares / 1e6 + nd_m
    value = ev / last.ltm_ebitda
    line = at_price_line(price=float(price), price_as_of=_iso(si.as_of), shares=float(shares),
                         shares_basis=shares_basis, net_debt=nd_m, ltm_ebitda=last.ltm_ebitda,
                         ltm_through=last.balance_sheet_date, value=value)
    return EvEbitdaAtPrice(
        value=round(value, 6), price=float(price), price_as_of=_iso(si.as_of),
        shares=float(shares), shares_basis=shares_basis,
        net_debt=round(nd_m, 3), net_debt_source="EDGAR: " + nd[1], ev=round(ev, 3),
        ltm_ebitda=round(last.ltm_ebitda, 3), ltm_through=last.balance_sheet_date, line=line,
        source_ref=(f"Assembler: ex-lease EV/EBITDA at the page's close "
                    f"({_iso(si.as_of) or 'date unstated'}) — price × {shares_basis} + EDGAR net "
                    f"debt excluding operating leases, ÷ CIQ LTM EBITDA to "
                    f"{last.balance_sheet_date}"))
