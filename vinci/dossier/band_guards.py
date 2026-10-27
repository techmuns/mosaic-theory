"""Band guards — does a committed multiple actually describe THIS company?

Fifth band-defect class (VITL, 2026-07-21): the CIQ Multiples export carried a ``TEV/LTM EBITDA``
row contradicted by its OWN ``TEV/LTM EBIT`` row — implied D&A ~$329M against $15M recorded,
systematic across every period. Nothing caught it: the parser read the labelled row correctly, the
revenue and EBIT rows on the same sheet reconciled to EDGAR exactly, and the band's periodicity /
span metadata was honest. The row itself was simply wrong — and a wrong denominator propagates
silently into ``anchor_base_value_per_share``, which is the number a human reads as the fundamental.

Two cross-checks that deliberately share NO input, so one vendor defect cannot satisfy both:

* :func:`sheet_coherence` — INTERNAL. TEV cancels out of the ratio of any two multiples read off
  ONE column, so the sheet alone implies an EBITDA margin, an EBIT margin, and the D&A margin
  between them. No market data, no EDGAR, no vintage question: a trip here is the export
  contradicting itself, and needs no other source to prove it.
* :func:`market_reconciliation` — EXTERNAL. ``(market cap + net debt) / current multiple`` is the
  EBITDA the multiple asserts the market is paying for; compare against what the company reported.

Both are ORDER-OF-MAGNITUDE screens, never precision tests. An LTM multiple sitting beside a
last-actual-FY financial disagrees by tens of percent on honest names as a matter of course, so
every bound sits far outside that noise — see the calibration table below.

A trip FLAGS and disqualifies; it never raises. Refusing to parse would cost the whole dossier over
one bad row (the other 95% of VITL's export is sound and reconciles), so the loud failure is the
same shape ``periodicity_mismatch`` already uses: stamp ``data_quality``, cap the leg at weak, and
refuse to publish a value derived from the tainted input.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

BAND_INCOHERENT = "band_incoherent"
BAND_UNRECONCILED = "band_unreconciled"

# --- calibration ------------------------------------------------------------------------------
# Set by FACE VALIDITY against the 2026-07-21 sweep of ALL committed bands (table in the PR), never
# by what would have flagged a name already disliked — no bound here has ever seen a forward return.
# Each sits near the GEOMETRIC midpoint of the worst HONEST reading and VITL's, so neither the
# honest names nor the real defect runs close to the line:
#
#   check                                honest worst       VITL     bound   headroom
#   implied D&A / revenue                CNXC   11.14%     41.91%      25%    2.2x / 1.7x
#   implied D&A / recorded D&A           EPAM    4.20x     35.53x       8x    1.9x / 4.4x
#   market-implied EBITDA / recorded     CNXC    1.41x      4.62x     2.5x    1.8x / 1.8x
#
# D&A as a share of revenue is bounded by ECONOMICS far more tightly than an EBITDA margin is (a
# 40%-margin software name is ordinary; a business depreciating 25% of revenue is not), which is why
# the internal ceiling sits on the D&A margin and not on the implied EBITDA margin itself.
_MAX_IMPLIED_DA_MARGIN = 0.25
_MAX_DA_RATIO = 8.0
_MAX_MARKET_RATIO = 2.5


#: A guard's OUTCOME — `schemas.CrossCheck`'s three states, spelled here because `schemas` imports
#: the anchor, which imports this module (a test holds the two equal). Both guards below return
#: nothing on a pass AND when they cannot run, so the flag alone cannot tell them apart.
BandOutcome = Literal["agree", "differ", "not_run"]


class BandChecks(BaseModel, frozen=True):
    """THE TWO ANCHOR-TIME GUARDS' OUTCOMES, stored on the anchor beside the flag (2026-10-27).
    ``agree``: the guard ran and the multiple describes this company; ``differ``: it ran and
    tripped (the flag is on ``data_quality``); ``not_run``: an input was missing — the ex-lease
    history carries no implied D&A margin, a recorded figure is absent or non-positive. An anchor
    that never reaches the guards (no own-history multiple, an R2 or R4 recipe) carries no block."""

    recorded_d_and_a: BandOutcome
    market_reconciliation: BandOutcome


class SheetCoherence(BaseModel, frozen=True):
    """What ONE column of the Multiples sheet implies about the company, plus any contradiction.

    The margins are the durable output: they are persisted on the band so the anchor can run the
    recorded-D&A comparison later, from committed JSON alone, without re-opening the workbook."""

    implied_ebitda_margin: float
    implied_ebit_margin: float
    implied_d_and_a_margin: float
    as_of: str | None = None
    flag: str | None = None          # BAND_INCOHERENT when the sheet contradicts itself
    detail: list[str] = []


class ReconCheck(BaseModel, frozen=True):
    """Market-anchored EBITDA vs reported EBITDA — the external half."""

    implied_ebitda: float
    recorded_ebitda: float
    ratio: float
    flag: str | None = None          # BAND_UNRECONCILED when they disagree by orders of magnitude
    detail: list[str] = []


def sheet_coherence(
    *, mult_revenue: float | None, mult_ebitda: float | None, mult_ebit: float | None,
    as_of: str | None = None,
) -> SheetCoherence | None:
    """The three TEV/LTM multiples off ONE column → the margins they imply, and whether they agree.

    ``None`` when a multiple is absent or non-positive: a sheet without a ``TEV/LTM EBIT`` row is a
    legitimate export variation (a coverage gap for this check, not a defect), and a negative
    multiple means a negative denominator, where the margin identity below stops holding.

    The identity: with a common TEV, ``EBITDA/revenue == mult_revenue / mult_ebitda`` — TEV cancels,
    so no absolute figure is needed. D&A is the gap between the two margins, and must be both
    non-negative (EBITDA ≥ EBIT, so ``mult_ebitda <= mult_ebit``) and economically sane."""
    if not (mult_revenue and mult_ebitda and mult_ebit):
        return None
    if mult_revenue <= 0 or mult_ebitda <= 0 or mult_ebit <= 0:
        return None

    m_ebitda = mult_revenue / mult_ebitda
    m_ebit = mult_revenue / mult_ebit
    m_da = m_ebitda - m_ebit
    detail: list[str] = []

    # (1) IDENTITY. D&A cannot be negative, so EBITDA cannot sit below EBIT. Catches a swapped or
    # mis-labelled row outright — no threshold, no calibration, nothing to tune.
    if m_da < 0:
        detail.append(
            f"implied EBITDA margin {m_ebitda:.2%} is BELOW implied EBIT margin {m_ebit:.2%} "
            f"(TEV/LTM EBITDA {mult_ebitda:.3f}x vs TEV/LTM EBIT {mult_ebit:.3f}x) — implies "
            "negative D&A; the two rows cannot both describe this company")
    # (2) MAGNITUDE. The VITL shape: an EBITDA row so low it implies the company depreciates a
    # plausible-looking business away. Sanity-checked against revenue, which needs no second source.
    elif m_da > _MAX_IMPLIED_DA_MARGIN:
        detail.append(
            f"implied D&A is {m_da:.2%} of revenue (EBITDA margin {m_ebitda:.2%} − EBIT margin "
            f"{m_ebit:.2%}), above the {_MAX_IMPLIED_DA_MARGIN:.0%} ceiling — TEV/LTM EBITDA "
            f"{mult_ebitda:.3f}x is not describing the same company as TEV/LTM EBIT "
            f"{mult_ebit:.3f}x")
    return SheetCoherence(
        implied_ebitda_margin=round(m_ebitda, 6), implied_ebit_margin=round(m_ebit, 6),
        implied_d_and_a_margin=round(m_da, 6), as_of=as_of,
        flag=BAND_INCOHERENT if detail else None, detail=detail)


def _d_and_a_runs(implied_d_and_a_margin: float | None, revenue: float | None,
                  recorded_d_and_a: float | None) -> bool:
    """Whether :func:`recorded_d_and_a_check` has the inputs to run — its one gate, shared with
    :func:`recorded_d_and_a_outcome` so the outcome and the flag cannot read it two ways."""
    return (implied_d_and_a_margin is not None and bool(revenue) and bool(recorded_d_and_a)
            and (revenue or 0.0) > 0 and (recorded_d_and_a or 0.0) > 0)


def recorded_d_and_a_check(
    *, implied_d_and_a_margin: float | None, revenue: float | None, recorded_d_and_a: float | None,
) -> tuple[str | None, list[str]]:
    """The sheet's implied D&A in dollars vs the D&A the company actually reported → (flag, detail).

    Runs at anchor time, where the recorded figures live; the implied margin arrives pre-computed on
    the committed band, so no workbook is re-opened. ``(None, [])`` when an input is missing or
    non-positive — an absent D&A tag is already its own flagged gap upstream, never a silent zero.

    Both sides are the SAME units (the caller's — $M throughout the anchor), because only their
    ratio is used."""
    if not _d_and_a_runs(implied_d_and_a_margin, revenue, recorded_d_and_a):
        return None, []
    assert implied_d_and_a_margin is not None and revenue and recorded_d_and_a  # narrowed above
    implied = implied_d_and_a_margin * revenue
    ratio = implied / recorded_d_and_a
    if 1 / _MAX_DA_RATIO <= ratio <= _MAX_DA_RATIO:
        return None, []
    return BAND_INCOHERENT, [
        f"Multiples sheet implies D&A of {implied:,.1f} against {recorded_d_and_a:,.1f} recorded "
        f"({ratio:,.1f}x) — outside the {_MAX_DA_RATIO:.0f}x band; the EV/EBITDA denominator does "
        "not match this company's own cost structure"]


def recorded_d_and_a_outcome(
    *, implied_d_and_a_margin: float | None, revenue: float | None, recorded_d_and_a: float | None,
) -> BandOutcome:
    """:func:`recorded_d_and_a_check`'s OUTCOME from the same inputs: not_run where it lacks one,
    else differ when it flags and agree when it does not — the flag's own decision, not a second."""
    if not _d_and_a_runs(implied_d_and_a_margin, revenue, recorded_d_and_a):
        return "not_run"
    flag, _detail = recorded_d_and_a_check(implied_d_and_a_margin=implied_d_and_a_margin,
                                           revenue=revenue, recorded_d_and_a=recorded_d_and_a)
    return "differ" if flag else "agree"


def reconciliation_outcome(recon: ReconCheck | None) -> BandOutcome:
    """:func:`market_reconciliation`'s OUTCOME: None (it could not run) is not_run, never a pass."""
    if recon is None:
        return "not_run"
    return "differ" if recon.flag else "agree"


def market_reconciliation(
    *, market_cap: float | None, net_debt: float | None, current_multiple: float | None,
    recorded_ebitda: float | None,
) -> ReconCheck | None:
    """EBITDA the CURRENT multiple asserts, vs EBITDA the company reported. ``None`` when an input
    is missing (nothing to check) or when reported EBITDA is non-positive (a loss-making name makes
    the ratio meaningless, and R1 never anchors one — the positivity guard sends it to R2 first).

    ``net_debt`` may be negative (net cash) — ordinary, not a gap; only ``None`` skips. This reads a
    market price ONLY to CHECK a multiple: no anchor value derives from it, so the anchor's base
    value per share stays the spot-independent fundamental it is documented to be."""
    if market_cap is None or net_debt is None or not current_multiple or not recorded_ebitda:
        return None
    if market_cap <= 0 or current_multiple <= 0 or recorded_ebitda <= 0:
        return None
    implied = (market_cap + net_debt) / current_multiple
    ratio = implied / recorded_ebitda
    detail: list[str] = []
    if not (1 / _MAX_MARKET_RATIO <= ratio <= _MAX_MARKET_RATIO):
        detail.append(
            f"market-implied EBITDA {implied:,.1f} vs {recorded_ebitda:,.1f} recorded "
            f"({ratio:,.2f}x) — outside the {_MAX_MARKET_RATIO}x band. TEV "
            f"{market_cap + net_debt:,.1f} (market cap {market_cap:,.1f} + net debt "
            f"{net_debt:,.1f}) ÷ current multiple {current_multiple:,.3f}x")
    return ReconCheck(
        implied_ebitda=round(implied, 3), recorded_ebitda=round(recorded_ebitda, 3),
        ratio=round(ratio, 4), flag=BAND_UNRECONCILED if detail else None, detail=detail)


def compose_flag(existing: str | None, new: str | None) -> str | None:
    """Join data-quality flags with ``+``, order-preserving and duplicate-free — a band can be both
    ``periodicity_mismatch`` AND ``band_incoherent``, and neither may mask the other."""
    parts = [p for p in (existing or "").split("+") if p]
    for p in (new or "").split("+"):
        if p and p not in parts:
            parts.append(p)
    return "+".join(parts) or None
