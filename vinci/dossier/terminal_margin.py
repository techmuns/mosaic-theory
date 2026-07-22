"""R2 — the TERMINAL-MARGIN recipe, for names R1 cannot anchor.

R1 re-rates a business to the median multiple of its own trading history on its own reported median
margin. That recipe needs a history worth reverting to. The R2 cohort has none — either the margin
history is negative (NCNO, MVST), or it is a ramp with a guided forward reset that no trailing
median describes (VITL), or the multiple series does not exist at all: FUBO's ``TEV/LTM EBITDA``,
``TEV/LTM EBIT`` and ``P/LTM EPS`` are ALL "NM" on a loss-making trailing year, so there is no band
to take a median of. Applying R1 to any of them would answer a question the data cannot support.

R2 asks a different question: **what is this business worth in the year it reaches a normal margin,
and what is that worth today?** The analyst supplies the terminal year, the terminal revenue and the
terminal margin per leg; the engine builds the bridge to a terminal value per share, discounts it at
a fixed house-wide hurdle, and applies the SAME reward/risk convention and 2:1 bar as R1 — the bar
does not move because the recipe did.

Three things R1 never had to model, all of which bite a pre-profit name:

* **DILUTION.** Years of stock compensation, plus any announced raise, land between today and the
  terminal year. Ignoring it values a share count that will not exist.
* **THE CASH BETWEEN HERE AND THERE.** A company that burns to breakeven arrives with more net debt
  than it has today, so terminal net debt starts from the burn, not from the current balance sheet.
* **SURVIVAL.** A terminal value is worthless if the company does not reach the terminal year. The
  survival gate is a HARD block on confirming a BUY, not an input to the ratio — an asymmetry
  computed on a company that runs out of money is not a cheap asymmetry, it is a wrong one.

The machine supplies every derived default (D&A ratio, share growth, burn) from source-bound facts
and the analyst may override each WITH A REASON — the same discipline as R1's margin: the machine
never proposes an assumption silently, and never accepts one without a recorded why.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from vinci.dossier.midcycle import BAR

# --- house-wide policy constants ---------------------------------------------------------------
# HURDLE is the PV companion to midcycle.BAR: both are fund-wide, both are operator-ratified, and
# neither is ever set per name. Ratified 2026-07-21 (STATE §7):
#
#   15% flat ≈ risk-free (~4.3%) + equity premium (~5%) + demanded excess. It is the midpoint of a
#   cohort CAPM-with-size-premium range (~12-17%), fixed house-wide so that NO NAME CAN PASS THE BAR
#   BY SHADING ITS OWN DISCOUNT RATE. Name-specific risk is expressed where it can be reviewed — in
#   the bear leg, in the survival gate, and in tier→confidence — never in the rate.
#
# A per-name hurdle would be the single easiest place to manufacture a pass, which is exactly why
# this is a module constant and not a record field.
HURDLE = 0.15

_USD_M = 1e6            # money is $M; share counts are raw. See terminal_value's UNITS note.
RECIPE_R2 = "R2_terminal_margin"
BASIS_EBITDA = "EV/EBITDA"
BASIS_EBIT = "EV/EBIT"
_BASES = (BASIS_EBITDA, BASIS_EBIT)

# TIER — a property of the BUSINESS, not of the answer. It feeds confidence at the verdict; it does
# NOT move the bar, because a lower bar for a worse business is how a fund talks itself into one.
TIER_A = "A"
TIER_B = "B"
TIER_DESC = {
    TIER_A: ("contracted or recurring revenue, gross-profitable, and self-funded to breakeven on "
             "the balance sheet it already has"),
    TIER_B: ("survival-gated or unproven unit economics — needs outside capital to reach the "
             "terminal year, or has not yet shown the gross margin the terminal case assumes"),
}

# THE one statement of the R2 arithmetic, stamped verbatim into every R2 record so a rendered card
# prints the recipe its numbers actually came from. Changing terminal_value() requires changing
# this LINE-FOR-LINE — the stamp/refuse guard makes a divergent record fail loud (the R1 precedent).
R2_FORMULA: tuple[str, ...] = (
    "EBIT_T = terminal revenue × terminal margin",
    "D&A_T = (latest-FY D&A ÷ latest-FY revenue) × terminal revenue",
    "EBITDA_T = EBIT_T + D&A_T",
    "EV_T = denominator_T × exit multiple   (denominator = EBITDA_T, or EBIT_T on EV/EBIT)",
    "net debt_T = current net debt + cumulative burn to breakeven",
    "equity_T = EV_T − net debt_T",
    "shares_T = current diluted × (1 + share growth)^years + announced-raise shares",
    "value_T = equity_T ÷ shares_T",
    "PV = value_T ÷ (1 + hurdle)^years",
)


class TerminalError(ValueError):
    """An R2 leg the machine refuses to compute — a degenerate input, never a silent fudge."""


@dataclass(frozen=True)
class TerminalLeg:
    """One analyst-supplied leg. Every field is the analyst's; the machine labels and refuses."""

    name: str                      # bear | base | bull
    years: float                   # years to the terminal year
    revenue: float                 # terminal revenue ($M)
    margin: float                  # terminal EBIT margin, decimal fraction
    multiple: float                # exit multiple, turns on the record's basis
    reason: str                    # WHY these terminal values — required, never blank


@dataclass(frozen=True)
class TerminalValue:
    """One leg's terminal-year bridge and its present value. Both are reported: the terminal value
    is what the analyst modelled, the PV is what the ratio uses, and conflating them is how a
    five-year story gets compared against a price paid today."""

    years: float
    ebit_t: float
    d_and_a_t: float
    ebitda_t: float
    denominator_t: float           # EBITDA_T, or EBIT_T on an EV/EBIT basis
    basis: str
    ev_t: float
    net_debt_t: float
    equity_t: float
    shares_t: float
    value_t: float                 # terminal value per share
    pv: float                      # discounted to today at HURDLE
    hurdle: float = HURDLE


@dataclass(frozen=True)
class Survival:
    """The gate. ``status`` is PASS or FAIL; a FAIL blocks a confirmed BUY and is not overridable
    by the arithmetic looking attractive."""

    status: str                    # "PASS" | "FAIL"
    burn: float | None             # annual cash burn ($M, positive) — None when FCF >= 0
    burn_basis: str
    burn_source: str
    cash: float
    facilities: float
    facilities_source: str | None
    runway_years: float | None
    years_to_breakeven: float | None
    announced_raise: bool
    raise_accession: str | None
    note: str
    detail: list[str] = field(default_factory=list)


def d_and_a_ratio(*, latest_d_and_a: float, latest_revenue: float) -> float:
    """D&A as a share of revenue, from the latest reported FY — the default the terminal year
    inherits. Held as a RATIO rather than a level because the terminal year's revenue is by
    construction not today's; carrying a dollar D&A forward would understate it exactly when the
    business has scaled. The analyst overrides with a reason where capital intensity is changing."""
    if latest_revenue <= 0:
        raise TerminalError("latest revenue must be > 0 to derive a D&A ratio — refusing to "
                            "divide by a non-positive denominator")
    return latest_d_and_a / latest_revenue


def share_growth(diluted_by_year: dict[int, float]) -> float:
    """Trailing 3-year CAGR of the diluted share count, FLOORED AT ZERO.

    The floor is deliberate and asymmetric. A company that shrank its count through buybacks is not
    evidence it will keep shrinking, and projecting negative dilution into a terminal year is a
    silent gift to the valuation — the one direction the error must never run for a pre-profit name
    that will more likely be issuing stock. Fewer than two observations → 0.0 (no trend to read).
    """
    years = sorted(diluted_by_year)
    if len(years) < 2:
        return 0.0
    window = years[-4:]                    # up to 4 points => up to a 3-year span
    first, last = diluted_by_year[window[0]], diluted_by_year[window[-1]]
    span = window[-1] - window[0]
    if span <= 0 or first <= 0 or last <= 0:
        return 0.0
    return max(0.0, float((last / first) ** (1.0 / span)) - 1.0)


def survival_gate(
    *, fcf: float | None, fcf_basis: str, fcf_source: str, cash: float,
    facilities: float = 0.0, facilities_source: str | None = None,
    years_to_breakeven: float | None = None, announced_raise: bool = False,
    raise_accession: str | None = None, going_concern_stated: bool = False,
    going_concern_accession: str | None = None, burn_override: float | None = None,
    burn_override_basis: str | None = None, latest_period_fcf: float | None = None,
) -> Survival:
    """Can this company reach its terminal year? PASS or FAIL, on stated inputs.

    ``fcf >= 0`` is a TRIVIAL PASS and says so — a company funding itself has no runway question,
    and dressing that up as a computed gate would imply a risk assessment nobody made.

    Otherwise burn is the magnitude of negative free cash flow, runway is ``(cash + committed
    undrawn facilities) ÷ burn``, and the gate FAILS when runway falls short of the analyst's
    years-to-breakeven with no announced or committed raise. A raise counts ONLY with an accession:
    an intention reported in a press cycle is not committed capital, and the whole point of the gate
    is to refuse the assumption that money will appear.
    """
    detail: list[str] = []

    # A SIGN CONTRADICTION between the trailing annual figure and the latest period is always
    # printed, whatever the gate concludes. MVST's trailing year read +$56.1M while its latest
    # quarter annualised to -$102.6M; a reader shown only the annual number would draw the
    # opposite conclusion from the same company.
    if fcf is not None and latest_period_fcf is not None and (fcf >= 0) != (latest_period_fcf >= 0):
        detail.append(
            f"WARNING: trailing free cash flow {fcf:+,.1f} and the latest period "
            f"{latest_period_fcf:+,.1f} have OPPOSITE SIGNS — the trailing figure is "
            "describing a period that has ended")

    # GOING CONCERN FORBIDS THE TRIVIAL PASS. A filer that has told the SEC there is substantial
    # doubt about its ability to continue has answered the runway question itself, and a positive
    # TRAILING free cash flow cannot overturn it — the disclosure is about the future, the cash
    # flow is about the past. MVST is the falsifier: trailing +$56.1M, going-concern stated, latest
    # quarter annualising to -$102.6M. Without this branch the gate returned "the company funds
    # itself and has no runway question" on exactly that name.
    if going_concern_stated:
        detail.append(
            "going concern: the filer states substantial doubt about its ability to continue"
            + (f" (accession {going_concern_accession})" if going_concern_accession
               else " — NO ACCESSION on file"))
        if burn_override is None:
            return Survival(
                status="FAIL", burn=None, burn_basis=(burn_override_basis or fcf_basis),
                burn_source=fcf_source, cash=cash, facilities=facilities,
                facilities_source=facilities_source, runway_years=None,
                years_to_breakeven=years_to_breakeven, announced_raise=announced_raise,
                raise_accession=raise_accession,
                note="going concern stated and NO burn override supplied — the trailing figure "
                     "cannot be used to clear a company whose own filing raises the doubt; state "
                     "the current burn",
                detail=detail)
        fcf = -abs(burn_override)          # evaluate on the stated burn, never the trailing sign
        fcf_basis = burn_override_basis or fcf_basis
    elif burn_override is not None:
        fcf = -abs(burn_override)
        fcf_basis = burn_override_basis or fcf_basis

    if fcf is not None and fcf >= 0:
        return Survival(
            status="PASS", burn=None, burn_basis=fcf_basis, burn_source=fcf_source, cash=cash,
            facilities=facilities, facilities_source=facilities_source, runway_years=None,
            years_to_breakeven=years_to_breakeven, announced_raise=announced_raise,
            raise_accession=raise_accession,
            note=(f"trivial pass — free cash flow is positive ({fcf:,.1f}, {fcf_basis}); the "
                  "company funds itself and has no runway question"),
            detail=detail)      # carries the sign-contradiction warning when one was raised
    if fcf is None:
        return Survival(
            status="FAIL", burn=None, burn_basis=fcf_basis, burn_source=fcf_source, cash=cash,
            facilities=facilities, facilities_source=facilities_source, runway_years=None,
            years_to_breakeven=years_to_breakeven, announced_raise=announced_raise,
            raise_accession=raise_accession,
            note="free cash flow UNKNOWN — the gate cannot clear a company whose burn is not "
                 "established; supply it with a basis, or pull the statement",
            detail=["fcf is None — refusing to assume solvency from an absent number"])
    burn = -fcf
    funds = cash + facilities
    runway = funds / burn if burn > 0 else None
    detail.append(f"runway = (cash {cash:,.1f} + committed undrawn facilities {facilities:,.1f}) "
                  f"÷ burn {burn:,.1f} = {runway:,.2f}y" if runway is not None else
                  "burn is zero — runway undefined")
    if years_to_breakeven is None:
        return Survival(
            status="FAIL", burn=burn, burn_basis=fcf_basis, burn_source=fcf_source, cash=cash,
            facilities=facilities, facilities_source=facilities_source, runway_years=runway,
            years_to_breakeven=None, announced_raise=announced_raise,
            raise_accession=raise_accession,
            note="years-to-breakeven not set — a burning company cannot be cleared without one",
            detail=detail)
    short = runway is not None and runway < years_to_breakeven
    if short and not announced_raise:
        note = (f"FAIL — {runway:,.2f}y of runway against {years_to_breakeven:,.2f}y to breakeven, "
                "and no announced or committed raise on file")
        status = "FAIL"
    elif short:
        note = (f"PASS on an announced raise — {runway:,.2f}y of runway against "
                f"{years_to_breakeven:,.2f}y to breakeven, bridged by the raise at "
                f"{raise_accession or 'NO ACCESSION'}")
        status = "PASS"
        if not raise_accession:
            status = "FAIL"
            note = (f"FAIL — runway {runway:,.2f}y falls short of {years_to_breakeven:,.2f}y and "
                    "the raise carries NO ACCESSION; an announced intention is not committed "
                    "capital")
    else:
        note = (f"PASS — {runway:,.2f}y of runway covers {years_to_breakeven:,.2f}y to breakeven"
                if runway is not None else "PASS — no burn")
        status = "PASS"
    return Survival(
        status=status, burn=burn, burn_basis=fcf_basis, burn_source=fcf_source, cash=cash,
        facilities=facilities, facilities_source=facilities_source, runway_years=runway,
        years_to_breakeven=years_to_breakeven, announced_raise=announced_raise,
        raise_accession=raise_accession, note=note, detail=detail)


def terminal_value(
    leg: TerminalLeg, *, basis: str, d_and_a_ratio_: float, net_debt_now: float,
    burn_to_breakeven: float, shares_now: float, g_sbc: float, raise_shares: float = 0.0,
    hurdle: float = HURDLE,
) -> TerminalValue:
    """One leg's terminal bridge and its present value.

    UNITS, stated because this is where the money is lost: every monetary input is **$M**, and
    ``shares_now``/``raise_shares`` are raw share **COUNTS** (the R1 convention — the anchor stores
    ``diluted_shares`` as a count, e.g. 109_458_472). The engine therefore scales equity to dollars
    ONCE, here, before dividing. Skipping that step yields a value per share ~1e6 too small, which
    is not a number a reviewer catches by eye because it is silently plausible as "cheap" — the
    R1 anchor sidesteps the same trap by scaling at its own call site. Pinned by a magnitude test.

    ``burn_to_breakeven`` is cumulative cash consumed before the company funds itself, and it only
    ever ADDS to terminal net debt: cash spent to get there is not available to equity when it
    arrives. ``g_sbc`` compounds the share count over the horizon and any announced raise adds on
    top, because a raise is a discrete event, not a growth rate."""
    if basis not in _BASES:
        raise TerminalError(f"unknown multiple basis {basis!r} — expected one of {_BASES}")
    if leg.years <= 0:
        raise TerminalError(f"{leg.name}: years to terminal must be > 0 — a terminal year that is "
                            "today is not a forecast, and the discount would be a no-op")
    if leg.revenue <= 0:
        raise TerminalError(f"{leg.name}: terminal revenue must be > 0")
    if leg.multiple <= 0:
        raise TerminalError(f"{leg.name}: exit multiple must be > 0")
    if not (leg.reason or "").strip():
        raise TerminalError(f"{leg.name}: a terminal leg needs a stated reason — refusing to "
                            "record modelled terminal values with no recorded why")
    if shares_now <= 0:
        raise TerminalError("current diluted shares must be > 0")
    if hurdle <= -1:
        raise TerminalError("hurdle must be > -100%")

    ebit_t = leg.revenue * leg.margin
    d_and_a_t = d_and_a_ratio_ * leg.revenue
    ebitda_t = ebit_t + d_and_a_t
    denom = ebitda_t if basis == BASIS_EBITDA else ebit_t
    if denom <= 0:
        raise TerminalError(
            f"{leg.name}: terminal {basis} denominator is {denom:,.2f} — a multiple on a "
            "non-positive denominator produces a negative enterprise value, which is not a "
            "valuation; model a higher terminal margin or use the other basis")
    ev_t = denom * leg.multiple
    net_debt_t = net_debt_now + burn_to_breakeven
    equity_t = ev_t - net_debt_t
    shares_t = shares_now * (1.0 + g_sbc) ** leg.years + raise_shares
    if shares_t <= 0:
        raise TerminalError(f"{leg.name}: terminal share count is non-positive")
    value_t = equity_t * _USD_M / shares_t     # $M -> $, then ÷ a raw share count
    return TerminalValue(
        years=leg.years, ebit_t=ebit_t, d_and_a_t=d_and_a_t, ebitda_t=ebitda_t,
        denominator_t=denom, basis=basis, ev_t=ev_t, net_debt_t=net_debt_t, equity_t=equity_t,
        shares_t=shares_t, value_t=value_t, pv=value_t / (1.0 + hurdle) ** leg.years,
        hurdle=hurdle)


__all__ = [
    "BAR", "BASIS_EBIT", "BASIS_EBITDA", "HURDLE", "R2_FORMULA", "RECIPE_R2", "TIER_A", "TIER_B",
    "TIER_DESC", "Survival", "TerminalError", "TerminalLeg", "TerminalValue", "d_and_a_ratio",
    "share_growth", "survival_gate", "terminal_value",
]
