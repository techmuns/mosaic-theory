"""The R1 screening anchor, split into a MARGIN effect and a MULTIPLE effect (W61, 2026-11-18).

WHY. Since W50 the anchor prices TODAY'S EV/EBITDA multiple, struck on CURRENT EBITDA, on a
MID-CYCLE EBITDA: the last twelve months' revenue at the margin's own ten-year median. One blended
level hides which of the two did the work. A name whose margin rose structurally (LLY: mid-cycle
EBITDA 0.60x current) reads far below a value the market puts on it, a name at a cyclical trough
(WERN: 1.29x) far above, and a thin equity stub (VRRM: net debt 77% of EV) magnifies a small
EBITDA gap into a large one per share. This module states the two causes as levels.

THE SPLIT. With m the multiple the anchor prices (the band's current), M the band's median beside
it, E_mid the anchor's EBITDA, E_cur the EBITDA m is STRUCK ON, ND the anchor's net debt and S its
share count, all $M to the last step:

    value at current EBITDA  V0 = (m × E_cur − ND) / S
    margin effect               = m × (E_mid − E_cur) / S
    multiple effect             = (M − m) × E_mid / S      — beside the anchor, never in it
    anchor at today's multiple  = V0 + margin effect                    (identity)
    anchor at the median        = V0 + margin effect + multiple effect  (identity)

INSIDE THE IMPLIEDVALUATION FENCE. Nothing here reads a price. V0 is the value today's multiple puts
on the EBITDA it is struck on, a LEVEL beside the anchor and never the price, so no term is a gap
to the price (`render._screening_context_lines`; operator 2026-11-13, #1004 item 3c: "Keep it off").

E_CUR IS THE MULTIPLE'S OWN DENOMINATOR, NEVER MARKET-IMPLIED. An EBITDA backed out of the page's
price and the anchor's bridge would fold the price's move since the multiple's close, and every
bridge difference, into "EBITDA". SMPL's close of 2026-10-27 predates a rise of about 28% to its
2026-11-11 price, so a market-implied EBITDA read its mid-cycle EBITDA as 0.92x current when it is
1.13x. So E_cur is read on the band's own lease basis:

* the ex-lease history: the observation whose multiple IS the band's current, its ``ltm_ebitda``
  (CIQ income-statement EBITDA over four quarters; the multiple is (TEV − leases) ÷ it, exactly);
* CIQ's TEV/LTM EBITDA history (rent immaterial): reported LTM EBITDA, only where
  ``valuation.ev_ebitda_basis`` MEASURES CIQ's TEV ÷ that multiple reproducing it (``reported`` or
  ``indistinguishable``, within its 5%), on the multiple the band carries.

Anything else is REFUSED, never substituted: GOOGL's CIQ 22.9x divides its TEV by $144.8bn, neither
its reported $185.5bn nor that plus rent. The multiple effect still stands there, since it reads no
current EBITDA.

Every threshold is set by face validity, never by what any name's figure would come to. This
module ranks nothing and no decision reads it. It is display and audit only.
"""
from __future__ import annotations

import math
from datetime import date
from typing import Any

from pydantic import BaseModel

_USD_M = 1e6

#: How many days the multiple's close may sit before the page's price date and still be "today's".
#: Face validity: a month is the shortest gap over which a share price commonly moves by as much as
#: the effects this split separates (a 30% annual volatility is about 9% a month), so past it V0 is
#: the value at that close, not at the page's date, and the page says so.
STALE_CLOSE_DAYS = 30
#: Net debt's share of the EV the current multiple puts on current EBITDA, above which the split
#: FLAGS leverage (a flag, never a refusal). Face validity: past a half, debt is the larger claim
#: on the enterprise, so a percentage error in any EV input — EBITDA or multiple — reaches the value
#: per share at least doubled.
LEVERAGE_FLAG_NET_DEBT_TO_EV = 0.5
#: How far the band's current may sit from the multiple `ev_ebitda_basis` measured and still be the
#: same multiple: that block stores the headline at one decimal (LLY 27.9 against 27.85306).
SAME_MULTIPLE_TOL = 0.05
#: `ev_ebitda_basis.reading`s under which CIQ's multiple is struck on reported LTM EBITDA.
REPORTED_READINGS = frozenset({"reported", "indistinguishable"})
#: How far the split's anchor may sit from the anchor's own published value and still be the same
#: number: the published value is rounded to four decimals, its inputs to six (MCK: $0.006).
REPRODUCE_TOL = 0.01

BASIS = ("V0 = (m × E_cur − ND) / S; margin effect = m × (E_mid − E_cur) / S; multiple effect = "
         "(M − m) × E_mid / S. The anchor at today's multiple = V0 + margin effect; at the median "
         "= V0 + margin effect + multiple effect. m and M are the band's current and median; "
         "E_mid = LTM revenue × the median margin + D&A (the anchor's EBITDA); E_cur = the EBITDA "
         "m is struck on; ND and S are the anchor's net debt and share count. No term reads a "
         "price. The margin effect carries every difference between E_mid and E_cur, including "
         "the GAAP-versus-CIQ basis the mid-cycle gap reports.")


class AnchorGapSplit(BaseModel, frozen=True):
    """The anchor as V0 plus a margin effect, with the multiple effect beside it (W61).

    Money is $M and per-share figures are $ per share. ``refusal`` is set when the EBITDA today's
    multiple is struck on is not identified on the page. Then the three terms that need it are
    None, and the multiple effect, which does not, still stands."""

    current_multiple: float              # m — the band's current, the multiple the anchor prices
    median_multiple: float               # M — the band's trailing median, beside it
    multiple_close: str | None           # the close m is struck at
    price_date: str | None               # the page's price date, the cut the anchor reads
    close_age_days: int | None           # price_date − multiple_close
    stale_close: bool | None             # close_age_days > STALE_CLOSE_DAYS
    midcycle_ebitda: float               # E_mid, $M
    midcycle_ebitda_source: str
    current_ebitda: float | None         # E_cur, $M
    current_ebitda_source: str | None    # what makes it m's denominator
    current_ebitda_through: str | None   # the end of its four quarters, where the page states it
    net_debt: float                      # ND, $M
    shares: float                        # S
    value_at_current_ebitda: float | None  # V0, per share
    margin_effect: float | None            # per share
    multiple_effect: float                 # per share
    anchor_at_current: float               # V0 + margin effect, per share
    anchor_at_median: float                # V0 + margin effect + multiple effect, per share
    net_debt_to_ev: float | None           # ND ÷ (m × E_cur)
    equity_sensitivity: float | None       # 1 ÷ (1 − net_debt_to_ev), % per 1% of EV; V0 ≤ 0: None
    leverage_flag: bool | None             # net_debt_to_ev > LEVERAGE_FLAG_NET_DEBT_TO_EV
    refusal: str | None = None
    basis: str = BASIS
    # The two renderers print these VERBATIM, written once here as `midcycle_gap.read` is: the
    # main-body line, its two flags (None when unset) and the on-demand tier's arithmetic.
    read: str = ""
    stale_line: str | None = None
    leverage_line: str | None = None
    arithmetic: list[str] = []


def _money(v: float) -> str:
    """$M, sign in front of the symbol: −$3,133M, never $-3,133M."""
    return f"{'−' if v < 0 else ''}${abs(v):,.0f}M"


def _ps(v: float) -> str:
    """Dollars per share, sign in front of the symbol."""
    return f"{'−' if v < 0 else ''}${abs(v):,.2f}"


def _m(v: Any, digits: int = 1) -> str:
    """A figure the page may lack, as $M digits or "unstated" — never a stated zero."""
    x = _num(v)
    return "unstated" if x is None else f"{x:,.{digits}f}"


def _days(n: int) -> str:
    """A day count in words: 1 day, 2 days."""
    return f"{n} day{'' if n == 1 else 's'}"


def _n(v: float) -> str:
    """A $M figure in the arithmetic, the minus a true one: −114,767.0, never -114,767.0."""
    return f"{'−' if v < 0 else ''}{abs(v):,.1f}"


def _words(s: AnchorGapSplit, *, revenue: float, margin: float, d_and_a: float) -> tuple[
        str, str | None, str | None, list[str]]:
    """The main-body line, the stale and leverage flags (None when unset) and the arithmetic
    tier, from the split's own numbers. Levels only: no term is set against a price (the
    ImpliedValuation fence)."""
    m, mm = s.current_multiple, s.median_multiple
    at_median = (f"At the {mm:.1f}x median it would be {_ps(abs(s.multiple_effect))} "
                 f"{'lower' if s.multiple_effect < 0 else 'higher'}, not used.")
    stale = lev = None
    if s.stale_close and s.close_age_days is not None:   # stale is set only from a measured age
        stale = (f"Today's multiple is the close of {s.multiple_close}, "
                 f"{_days(s.close_age_days)} "
                 f"before the page's stored close of {s.price_date}"
                 + (": the value on current EBITDA is that day's." if s.refusal is None else "."))
    if s.leverage_flag and s.net_debt_to_ev is not None:
        lev = (f"Net debt is {s.net_debt_to_ev:.0%} of the EV today's multiple puts on current "
               f"EBITDA, so each 1% of EBITDA or multiple moves the value per share "
               f"{s.equity_sensitivity:.1f}%." if s.equity_sensitivity is not None else
               "Net debt exceeds the EV today's multiple puts on current EBITDA: the value on "
               "current EBITDA is negative, and how far a 1% move in EBITDA or multiple carries "
               "per share is undefined.")
    lines = [f"m = {m:.4f}x, today's multiple (the close of {s.multiple_close or 'date unstated'})"
             f"; M = {mm:.4f}x, the median beside it, never used.",
             f"E_mid = {revenue:,.1f} × {margin:.4%} + {d_and_a:,.1f} = {_money(s.midcycle_ebitda)}"
             " — LTM revenue × the median margin + D&A, the anchor's EBITDA."]
    if s.refusal is not None or s.current_ebitda is None or s.margin_effect is None \
            or s.value_at_current_ebitda is None:
        read = (f"The screen value, {_ps(s.anchor_at_current)} at {m:.1f}x, is not split: "
                f"{s.refusal}. {at_median}")
        lines += [f"E_cur: not identified — {s.refusal}.",
                  f"multiple effect = ({mm:.4f} − {m:.4f}) × {s.midcycle_ebitda:,.1f} ÷ "
                  f"{s.shares:,.0f} shares = {_ps(s.multiple_effect)}, beside the anchor.",
                  f"screen value = ({m:.4f} × {s.midcycle_ebitda:,.1f} − net debt "
                  f"{_n(s.net_debt)}) ÷ {s.shares:,.0f} = {_ps(s.anchor_at_current)}; at the "
                  f"median {_ps(s.anchor_at_median)}."]
        return read, stale, lev, lines
    ratio = s.midcycle_ebitda / s.current_ebitda
    # THE APPROVED LINE (operator 2026-11-18, on the W61 preview: "Approve, shorter line"): its
    # shape is fixed; the margin sign, "lower"/"higher" and the ratio follow the numbers.
    read = (f"Screen value {_ps(s.anchor_at_current)} at today's {m:.1f}x = "
            f"{_ps(s.value_at_current_ebitda)} on current EBITDA ({_money(s.current_ebitda)}) "
            f"{'−' if s.margin_effect < 0 else '+'} {_ps(abs(s.margin_effect))} margin reversion "
            f"(mid-cycle {ratio:.2f}× current). Median {mm:.1f}x: "
            f"{_ps(abs(s.multiple_effect))} {'lower' if s.multiple_effect < 0 else 'higher'} "
            "(not used).")
    ev0 = m * s.current_ebitda
    lines += [
        f"E_cur = {_money(s.current_ebitda)} — {s.current_ebitda_source}.",
        f"V0 = ({m:.4f} × {s.current_ebitda:,.1f} − net debt {_n(s.net_debt)}) ÷ "
        f"{s.shares:,.0f} shares = {_ps(s.value_at_current_ebitda)}.",
        f"margin effect = {m:.4f} × ({s.midcycle_ebitda:,.1f} − {s.current_ebitda:,.1f}) ÷ "
        f"{s.shares:,.0f} = {_ps(s.margin_effect)}.",
        f"multiple effect = ({mm:.4f} − {m:.4f}) × {s.midcycle_ebitda:,.1f} ÷ {s.shares:,.0f} = "
        f"{_ps(s.multiple_effect)}, beside the anchor, never in it.",
        f"V0 + margin effect = {_ps(s.anchor_at_current)}, the screen value; + multiple effect = "
        f"{_ps(s.anchor_at_median)}, the value at the median.",
        f"net debt ÷ EV = {_n(s.net_debt)} ÷ {ev0:,.1f} = "
        f"{'−' if s.net_debt / ev0 < 0 else ''}{abs(s.net_debt / ev0):.3f}; "
        f"flagged above {LEVERAGE_FLAG_NET_DEBT_TO_EV:g}.",
        f"the multiple's close {s.multiple_close or 'unstated'}, the page's stored close "
        f"{s.price_date or 'unstated'}: "
        + (f"the multiple's close is {_days(-s.close_age_days)} AFTER it; stale above "
           f"{STALE_CLOSE_DAYS}." if s.close_age_days is not None and s.close_age_days < 0 else
           f"{_days(s.close_age_days)}; stale above {STALE_CLOSE_DAYS}."
           if s.close_age_days is not None else "no age measured."),
    ]
    return read, stale, lev, lines


def _iso(d: Any) -> str | None:
    if d is None:
        return None
    return d.isoformat() if hasattr(d, "isoformat") else str(d)


def _num(v: Any) -> float | None:
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(float(v)):
        return None
    return float(v)


def current_ebitda(mechanical: dict[str, Any], *, ex_lease: bool, current: float
                   ) -> tuple[float, str, str | None, str | None] | str:
    """The EBITDA ``current`` is struck on, on the band's own lease basis, read off the committed
    mechanical layer. Returns ``(E_cur $M, source, four quarters through, the multiple's close)``,
    or the reason it is not identified. Never market-implied, never a substitute."""
    val = mechanical.get("valuation") or {}
    if ex_lease:
        lb = val.get("lease_basis") or {}
        obs = [o for o in (lb.get("observations") or []) if isinstance(o, dict)
               and (mo := _num(o.get("multiple"))) is not None
               and abs(mo - current) <= 1e-6 * max(1.0, abs(current))]
        if not obs:
            return ("no ex-lease observation carries the band's current multiple "
                    f"({current:g}x), so the EBITDA it is struck on is not on the page")
        o = obs[-1]
        e = _num(o.get("ltm_ebitda"))
        if e is None or e <= 0:
            return (f"the ex-lease observation of {o.get('pricing_date')} carries no positive LTM "
                    "EBITDA")
        src = (f"valuation.lease_basis.observations (the observation of "
               f"{o.get('pricing_date')}): CIQ Income Statement 'EBITDA' over four quarters to "
               f"{o.get('balance_sheet_date')}, "
               f"the denominator of the ex-lease multiple {current:g}x = (TEV "
               f"{_m(o.get('tev'))} − leases {_m(o.get('leases_in_tev'))}) ÷ {e:,.1f}")
        return e, src, _iso(o.get("balance_sheet_date")), _iso(o.get("pricing_date"))
    eb = val.get("ev_ebitda_basis")
    if not isinstance(eb, dict):
        return ("the page carries no valuation.ev_ebitda_basis, so which EBITDA CIQ's multiple "
                "divides is not measured")
    mult = _num(eb.get("multiple"))
    if mult is None or abs(mult - current) > SAME_MULTIPLE_TOL + 1e-9:
        return (f"valuation.ev_ebitda_basis measured a {mult}x multiple, not the band's current "
                f"{current:g}x, so it does not say what this one divides")
    reading = eb.get("reading")
    e = _num(eb.get("reported_ltm_ebitda"))
    if reading not in REPORTED_READINGS:
        what = ("reported LTM EBITDA plus rent, which the anchor's EBITDA does not carry"
                if reading == "ebitda_plus_rent" else "neither reported LTM EBITDA nor that plus "
                "rent")
        return (f"CIQ's {mult:g}x divides TEV ${_m(eb.get('tev'), 0)}M by "
                f"${_m(eb.get('implied_denominator'), 0)}M: {what} "
                f"(valuation.ev_ebitda_basis: {reading}), so the EBITDA it is struck on is not "
                f"identified")
    if e is None or e <= 0:
        return "reported LTM EBITDA is not positive"
    src = (f"mechanical.financial_summary LTM 'EBITDA ($M)' (CIQ), which CIQ's TEV ÷ {mult:g}x "
           f"reproduces (valuation.ev_ebitda_basis: {reading}; "
           f"${_m(eb.get('implied_denominator'), 0)}M implied, TEV as "
           f"of {eb.get('tev_as_of')})")
    return e, src, None, None


def gap_split(mechanical: dict[str, Any], *, ex_lease: bool, current: float, median: float,
              close: str | None, revenue: float, margin: float, d_and_a: float,
              net_debt: float, shares: float, price_date: date | None) -> AnchorGapSplit:
    """The split, from the anchor's own inputs ($M; ``shares`` a count) and the committed
    mechanical layer. Pure arithmetic: never fetches, never reads a price."""
    if shares <= 0:
        raise ValueError("shares must be > 0")
    e_mid = revenue * margin + d_and_a
    per = _USD_M / shares
    at_current = (current * e_mid - net_debt) * per
    mult_effect = (median - current) * e_mid * per
    found = current_ebitda(mechanical, ex_lease=ex_lease, current=current)
    v0 = margin_effect = e_cur = nd_ev = sens = None
    lev: bool | None = None
    src = through = refusal = None
    if isinstance(found, str):
        refusal = found
    else:
        e_cur, src, through, obs_close = found
        close = obs_close or close
        ev0 = current * e_cur
        v0 = (ev0 - net_debt) * per
        margin_effect = current * (e_mid - e_cur) * per
        nd_ev = net_debt / ev0
        sens = ev0 / (ev0 - net_debt) if ev0 > net_debt else None
        lev = nd_ev > LEVERAGE_FLAG_NET_DEBT_TO_EV
    age = None
    if price_date is not None and close is not None:
        try:   # a display field: a close in another shape states no age, never sinks the anchor
            age = (price_date - date.fromisoformat(close[:10])).days
        except ValueError:
            age = None
    split = AnchorGapSplit(
        current_multiple=current, median_multiple=median, multiple_close=close,
        price_date=_iso(price_date), close_age_days=age,
        stale_close=None if age is None else age > STALE_CLOSE_DAYS,
        midcycle_ebitda=round(e_mid, 3),
        midcycle_ebitda_source=(f"anchor ltm_revenue × margin + d_and_a: {revenue:,.3f} × "
                                f"{margin:.6f} + {d_and_a:,.3f} ($M)"),
        current_ebitda=None if e_cur is None else round(e_cur, 3), current_ebitda_source=src,
        current_ebitda_through=through, net_debt=round(net_debt, 3), shares=shares,
        value_at_current_ebitda=None if v0 is None else round(v0, 4),
        margin_effect=None if margin_effect is None else round(margin_effect, 4),
        multiple_effect=round(mult_effect, 4), anchor_at_current=round(at_current, 4),
        anchor_at_median=round(at_current + mult_effect, 4),
        net_debt_to_ev=None if nd_ev is None else round(nd_ev, 6),
        equity_sensitivity=None if sens is None else round(sens, 4), leverage_flag=lev,
        refusal=refusal)
    read, stale, lev_line, lines = _words(split, revenue=revenue, margin=margin,
                                          d_and_a=d_and_a)
    return split.model_copy(update={"read": read, "stale_line": stale, "leverage_line": lev_line,
                                    "arithmetic": lines})


def reproduces(split: AnchorGapSplit, published: float, statistic: str | None) -> bool:
    """Whether the split rebuilds the anchor's published value: at today's multiple for an anchor
    derived since W50 (``statistic`` "current"), at the median for one derived before."""
    want = split.anchor_at_current if statistic == "current" else split.anchor_at_median
    return abs(want - published) <= REPRODUCE_TOL
