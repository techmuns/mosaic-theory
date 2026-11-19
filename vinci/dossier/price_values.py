"""THE FAST VALUES AT THE PAGE'S OWN CLOSE (2026-11-19; operator: "Yes, start there").

THE AUDIT (coordinator B, main e6a6c318, the 26 committed pages). The page's market cap, its TEV
and the name's "current" multiples came from S&P Capital IQ's MANUAL comps export, downloaded by
hand weeks apart, and a 45-day clock on that export guarded them. VRRM's Snapshot read "cap $333M
(2026-11-06) ⚠ implies $2.19/sh vs CMP (+31.9%)" beside a $1.66 close, and passed the clock at 13
days. Expert practice is the reverse: the fast values come from the automated daily feed, and a
vendor export supplies the slow data, is refreshed on EVENTS, and is dated wherever it is shown.

THE CONSTRUCTION — one, here, for every consumer:
  market cap at the page's price = the page's close (``stock_info.price``, at ``stock_info.as_of``)
                                   × its point-in-time share count (``stock_info.shares_out``);
  TEV at the page's price        = that market cap + CIQ's CLAIMS on the enterprise: its comps TEV
                                   less its comps market cap — the comps name row's net debt.
It is `valuation_basis`'s `value_at_page_price` construction ("page price × point-in-time shares
outstanding + CIQ claims"), and the share count is the one that block and the anchor read. The
claims are slow balance-sheet items (debt less cash), so they stay CIQ's, dated by its panel.

CIQ'S OWN CAP AND TEV STAY, DATED, AS CROSS-CHECKS — ``stock_info.market_cap`` at
``market_cap_as_of``, ``implied_expectations.tev`` at ``tev_as_of``. A difference beyond
`freshness.RECONCILE_TOLERANCE` FLAGS; a whole-number ratio is a share-basis change the build
refuses (`freshness.check_freshness`, unchanged). Neither ever supplies the number.

NOTHING IS IMPUTED. A page with no close, no share count or no claims gets an UNKNOWN naming what
is absent — never CIQ's figure in its place, never zero claims.

NOT MOVED HERE (operator, 2026-11-19 — later steps): the R1 screening anchor's "today's multiple"
(`anchor`, `anchor_split`), the scenario proposal's base multiple (`propose`). And the 2026-11-13
fence holds: nothing here sets the anchor against the price.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from vinci.dossier.freshness import RECONCILE_TOLERANCE, reconcile_cap
from vinci.dossier.schemas import (
    CapCrossCheck,
    ImpliedExpectationRow,
    ImpliedExpectations,
    Sourced,
)

_USD_M = 1e6

#: The construction, named once — both the TEV's source_ref and the record cite it.
TEV_AT_PRICE_BASIS = ("the page's close × its point-in-time share count, plus CIQ's claims (its "
                      "comps TEV less its comps market cap)")


def _num(x: Any) -> float | None:
    return float(x) if isinstance(x, (int, float)) and not isinstance(x, bool) else None


def _present(node: Any) -> float | None:
    """A Sourced node's value when it is PRESENT and a number, else None."""
    if isinstance(node, Mapping) and node.get("status") == "present":
        return _num(node.get("value"))
    return None


def _iso(v: Any) -> str | None:
    return str(v)[:10] if v else None


def cap_at_close(stock_info: Mapping[str, Any] | None) -> Sourced[float]:
    """The page's market cap, $M: its close × its point-in-time share count — or UNKNOWN naming
    what is absent."""
    si = stock_info or {}
    price, shares = _present(si.get("price")), _present(si.get("shares_out"))
    day = _iso(si.get("as_of"))
    absent = [n for n, v in (("a close", price), ("its date", day), ("a share count", shares))
              if not v]
    if absent or price is None or shares is None or day is None:
        return Sourced.unknown(note=(
            f"no market cap at the page's price — the page carries no {' and no '.join(absent)}; "
            "CIQ's comps figure is not put in its place"))
    if price <= 0 or shares <= 0:
        return Sourced.unknown(note=(
            f"no market cap at the page's price — close {price:g} × count {shares:g} is not a "
            "positive equity value"))
    shares_ref = (si.get("shares_out") or {}).get("source_ref") or "share count, source unstated"
    price_ref = (si.get("price") or {}).get("source_ref") or "EOD close"
    return Sourced.present(
        round(price * shares / _USD_M, 3),
        source_ref=(f"the page's close ${price:,.2f} ({price_ref}, {day}) × {shares:,.0f} shares "
                    f"({shares_ref})"))


def claims(mechanical: Mapping[str, Any]) -> Sourced[float]:
    """CIQ's claims on the enterprise beyond its equity, $M — its comps TEV less its comps market
    cap, which the comps workbook states as the name row's net debt — dated by the comps panel.
    UNKNOWN, never zero, where the name row carries none."""
    grid = (((mechanical.get("peer_comps") or {}).get("peer_grid") or {}).get("value")) or []
    row = next((r for r in grid if isinstance(r, Mapping) and r.get("is_name")), None)
    nd = _num(row.get("net_debt")) if row is not None else None
    day = _iso((mechanical.get("stock_info") or {}).get("market_cap_as_of"))
    if nd is None:
        return Sourced.unknown(note=(
            "no TEV at the page's price — the CIQ comps name row carries no net debt (CIQ's TEV "
            "less its market cap), so CIQ's claims are not known; none is imputed"))
    return Sourced.present(nd, source_ref=(
        f"CIQ Comparable Analysis→Financial Data, name row Net Debt — CIQ's TEV less its market "
        f"cap{f', as of {day}' if day else ''}"))


def tev_at_close(mechanical: Mapping[str, Any]) -> Sourced[float]:
    """The page's TEV, $M: its market cap at its own close plus CIQ's claims — or UNKNOWN naming
    which half is absent."""
    cap = cap_at_close(mechanical.get("stock_info"))
    cl = claims(mechanical)
    if cap.value is None:
        return Sourced.unknown(note=cap.note or "no market cap at the page's price")
    if cl.value is None:
        return Sourced.unknown(note=cl.note or "no CIQ claims")
    return Sourced.present(
        round(float(cap.value) + float(cl.value), 3),
        source_ref=(f"TEV at the page's close = market cap ${float(cap.value):,.1f}M "
                    f"({cap.source_ref}) + CIQ claims ${float(cl.value):,.1f}M ({cl.source_ref})"))


def ciq_tev(mechanical: Mapping[str, Any]) -> float | None:
    """CIQ's own simple TEV, $M — its comps market cap plus its claims, the TEV its comps
    multiples were struck at. None where either is absent."""
    cap = _present((mechanical.get("implied_valuation") or {}).get("market_cap"))
    cl = claims(mechanical)
    return cap + float(cl.value) if cap is not None and cl.value is not None else None


def tev_ratio(mechanical: Mapping[str, Any]) -> float | None:
    """TEV at the page's close ÷ CIQ's simple TEV — the factor a CIQ TEV multiple is restated at
    the page's price by, as `valuation_basis`'s ``value_at_page_price`` restates it. None where
    either TEV is absent or CIQ's is not positive."""
    at, ciq = tev_at_close(mechanical).value, ciq_tev(mechanical)
    if at is None or ciq is None or ciq <= 0:
        return None
    return float(at) / ciq


def _cross_check_ref(si: Mapping[str, Any]) -> str:
    ciq_day = _iso(si.get("market_cap_as_of"))
    return (f"freshness.reconcile_cap: CIQ Comparable Analysis→Financial Data, name Market "
            f"Capitalization Latest{f' (as of {ciq_day})' if ciq_day else ''}, against the page's "
            f"close ({(si.get('price') or {}).get('source_ref') or 'EOD close'}, "
            f"{_iso(si.get('as_of')) or 'date unstated'}) × "
            f"{(si.get('shares_out') or {}).get('source_ref') or 'its share count'}")


def cross_check(stock_info: Mapping[str, Any] | None) -> CapCrossCheck | None:
    """CIQ's comps cap against the page's close × count, or None where any of the three is absent
    (the page's own cap is then UNKNOWN, and the build's missing-input refusal names it)."""
    si = stock_info or {}
    ciq = _present(si.get("market_cap"))
    rc = reconcile_cap(cap_musd=ciq, shares=_present(si.get("shares_out")),
                       spot=_present(si.get("price")))
    if rc is None or ciq is None:
        return None
    return CapCrossCheck(
        ciq_market_cap=ciq, implied_price=round(rc.implied_price, 6), gap=round(rc.gap, 6),
        ratio=round(rc.ratio, 6), corporate_action=rc.corporate_action,
        beyond_tolerance=abs(rc.gap) > RECONCILE_TOLERANCE, tolerance=RECONCILE_TOLERANCE,
        note=rc.note(), source_ref=_cross_check_ref(si))


def restate_implied(ie: ImpliedExpectations, at: Sourced[float], *,
                    price_as_of: str | None) -> ImpliedExpectations:
    """The price-implied levels at the page's own close: each PEER-median row's level is the TEV
    at the close over the peer multiple. The name's own forward-multiple rows (``is_identity``)
    keep CIQ's TEV — that multiple was struck at it, so their level is the consensus by identity,
    not a price-inverted expectation — and so does the G5 probe. With no TEV at the close a peer
    row's level is UNKNOWN, never CIQ's TEV over the multiple."""
    rows: list[ImpliedExpectationRow] = []
    for r in ie.rows:
        if r.is_identity or r.multiple is None or r.multiple <= 0:
            rows.append(r)
            continue
        ref = (f"Assembler: implied {r.metric} — TEV at the page's close ÷ {r.label} "
               f"({r.multiple_source})")
        if at.value is None:
            rows.append(r.model_copy(update={
                "implied_level": None, "source_ref": ref,
                "note": f"no TEV at the page's close — {at.note}"}))
        else:
            rows.append(r.model_copy(update={
                "implied_level": round(float(at.value) / r.multiple, 1), "source_ref": ref}))
    return ie.model_copy(update={"rows": rows, "tev_at_close": at,
                                 "tev_close_date": price_as_of})


def cross_check_flag(ticker: str, stock_info: Mapping[str, Any] | None) -> str | None:
    """The QA flag a cap cross-check beyond tolerance raises, or None. A corporate action is the
    freshness gate's to refuse; this states drift, with both dates."""
    cc = cross_check(stock_info)
    if cc is None or not cc.beyond_tolerance or cc.corporate_action:
        return None
    si = stock_info or {}
    return (f"cap-cross-check: {ticker} CIQ's comps market cap ${cc.ciq_market_cap:,.1f}M (as of "
            f"{_iso(si.get('market_cap_as_of')) or 'date unstated'}) is {cc.gap:+.1%} from the "
            f"page's own close × share count ({_iso(si.get('as_of')) or 'date unstated'}), beyond "
            f"the {cc.tolerance:.0%} tolerance — the page's cap, TEV and the name's current "
            "multiples are struck at its close; CIQ's figure is the dated cross-check")
