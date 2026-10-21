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

Every threshold is set by face validity, never by what any name's figure would come to.
"""
from __future__ import annotations

from typing import Any

from vinci.dossier.schemas import EvEbitdaAtPrice, EvEbitdaBasis, MechanicalLayer, SourceStatus

#: How far the multiple's implied denominator may sit from a pairing and still reproduce it. The
#: rent is ANNUAL (CIQ's last fiscal year) against an LTM EBITDA, the multiple prints at one
#: decimal, and the comps TEV can sit days from the multiple's close — each worth a few percent.
#: Measured 2026-10-21: the 14 pages that reproduce EBITDA + rent do so within 0.7%–4.9%.
PAIRING_TOL = 0.05


def _iso(x: Any) -> str | None:
    """A page date as the ISO string these blocks store — `stock_info.as_of` is a `date`, the comps
    TEV's as-of a string; both are written one way."""
    if x is None:
        return None
    return x.isoformat() if hasattr(x, "isoformat") else str(x)


def _money(v: float) -> str:
    """$M with the sign in front of the symbol: a net-cash bridge reads −$3,133M, never $-3,133M."""
    return f"{'−' if v < 0 else ''}${abs(v):,.0f}M"


def _ltm_ebitda(mech: MechanicalLayer) -> float | None:
    """Reported LTM EBITDA, $M — the financial summary's structured `LTM` value, never a cell."""
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


def headline_basis(mech: MechanicalLayer) -> EvEbitdaBasis | None:
    """CIQ's headline TEV/LTM EBITDA, read against the two consistent-or-not pairings, or None when
    the page lacks a positive multiple, a snapshot TEV or a positive reported LTM EBITDA."""
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
    lb = val.lease_basis
    rent = lb.rent_expense if lb is not None and lb.rent_expense and lb.rent_expense > 0 else None
    tev, mult = float(ie.tev.value), float(ev.value)
    implied = tev / mult
    r_rep = implied / ltm
    r_rent = implied / (ltm + rent) if rent is not None else None
    ok_rep = abs(r_rep - 1) <= PAIRING_TOL
    ok_rent = r_rent is not None and abs(r_rent - 1) <= PAIRING_TOL
    fy = lb.rent_fiscal_year if lb is not None else None
    tev_day = _iso(ie.tev_as_of) or "date unstated"
    head = f"CIQ's {mult:.1f}x divides TEV ${tev:,.0f}M (comps, {tev_day}) by ${implied:,.0f}M"
    rent_txt = (f"reported LTM EBITDA ${ltm:,.0f}M + rent ${rent:,.0f}M"
                f"{f' (FY ending {fy})' if fy else ''} = ${ltm + rent:,.0f}M" if rent is not None
                else "")
    if ok_rep and ok_rent:
        assert rent is not None                          # `ok_rent` needs a measured rent
        reading = "indistinguishable"
        line = (f"{head}, which reproduces reported LTM EBITDA (${ltm:,.0f}M) and EBITDA plus rent "
                f"alike — rent is {rent / ltm:.1%} of EBITDA, too small for the pairing to change "
                "the reading.")
    elif ok_rent:
        assert r_rent is not None and rent is not None
        reading = "ebitda_plus_rent"
        line = (f"{head}: {rent_txt} ({abs(r_rent - 1):.1%} apart) — TEV WITH the operating "
                f"leases over EBITDA WITH rent added back, consistent on its own basis. It is NOT "
                f"a multiple of reported EBITDA (${ltm:,.0f}M, {1 - 1 / r_rep:.1%} below the "
                "denominator).")
    elif ok_rep:
        reading = "reported"
        line = (f"{head}: reported LTM EBITDA ${ltm:,.0f}M ({abs(r_rep - 1):.1%} apart) — a "
                "multiple of reported EBITDA.")
    else:
        reading = "not_reproduced"
        alt = (f" and {rent_txt} ({r_rent - 1:+.1%})" if rent is not None and r_rent is not None
               else "")
        line = (f"{head}, which reproduces neither pairing: reported LTM EBITDA ${ltm:,.0f}M "
                f"({r_rep - 1:+.1%}){alt}. Read CIQ's own denominator before comparing it with a "
                "multiple of reported EBITDA.")
    return EvEbitdaBasis(
        multiple=mult, tev=round(tev, 3), tev_as_of=_iso(ie.tev_as_of),
        implied_denominator=round(implied, 3), reported_ltm_ebitda=round(ltm, 3),
        rent=rent, rent_fiscal_year=fy, ratio_to_reported=round(r_rep, 6),
        ratio_to_reported_plus_rent=round(r_rent, 6) if r_rent is not None else None,
        reading=reading, tolerance=PAIRING_TOL, line=line)


def ex_lease_at_price(mech: MechanicalLayer, facts: dict[str, Any] | None,
                      ) -> EvEbitdaAtPrice | None:
    """R1's ex-lease EV/EBITDA at the page's stored close — only where R1 prices that basis (rent
    material and an ex-lease history built), and only from a complete bridge: a price, a
    point-in-time share count, net debt excluding operating leases (the anchor's builder) and the
    history's latest LTM EBITDA. None otherwise, never a partial figure."""
    from vinci.dossier.anchor import _lease_inclusive_net_debt  # the anchor's ONE bridge builder

    lb = mech.valuation.lease_basis
    si = mech.stock_info
    if lb is None or not lb.material or lb.ex_lease_band is None or si is None or not facts:
        return None
    last = next((o for o in reversed(lb.observations) if o.multiple is not None), None)
    if last is None or last.ltm_ebitda <= 0:
        return None
    price = si.price.value if si.price.status is SourceStatus.PRESENT else None
    shares = si.shares_out.value if si.shares_out.status is SourceStatus.PRESENT else None
    nd = _lease_inclusive_net_debt(facts, ex_operating_leases=True)
    if not price or not shares or nd is None or nd[0] is None:
        return None
    nd_m = nd[0] / 1e6
    ev = price * shares / 1e6 + nd_m
    value = ev / last.ltm_ebitda
    line = (f"at the page's ${price:,.2f} close ({_iso(si.as_of) or 'date unstated'}): "
            f"(${price:,.2f} × {shares:,.0f} shares + net debt {_money(nd_m)} excluding "
            f"operating leases) ÷ LTM EBITDA ${last.ltm_ebitda:,.0f}M (four quarters to "
            f"{last.balance_sheet_date}) = {value:.1f}x")
    return EvEbitdaAtPrice(
        value=round(value, 6), price=float(price), price_as_of=_iso(si.as_of),
        shares=float(shares),
        net_debt=round(nd_m, 3), net_debt_source="EDGAR: " + nd[1], ev=round(ev, 3),
        ltm_ebitda=round(last.ltm_ebitda, 3), ltm_through=last.balance_sheet_date, line=line)
