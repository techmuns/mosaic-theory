"""(phase 4) COST OF BORROWING — the weighted-average coupon, and what it deliberately excludes.

One of the cohort five. The input is the capital-structure instrument list the CIQ panel already
assembles: per tranche a `principal_musd`, a `coupon`, a `floating_rate` flag and a maturity. Those
are STRUCTURED fields on a committed artifact, so nothing here re-parses a rendered table.

THE COUPON CELL IS A DISPLAY STRING ("4.500%") and is read through `clean_num` — the ONE shared,
tested CIQ cell helper — never an ad-hoc regex. That is the house rule, and the reason for it is on
record: a thousands-blind re-parse of a `$1,101.80M` display string read it as `1` and fired a false
caveat.

WHAT IT REFUSES TO DO. A floating-rate tranche has no fixed coupon, and its cell is 'NA'. Averaging
it in at ZERO would drag the weighted average down in proportion to how much floating debt a name
carries — a fabricated number that looks most authoritative exactly where it is most wrong. Floating
principal is therefore reported as its own SHARE and never averaged. A name whose debt is entirely
floating has NO weighted-average coupon, and that is an answer rather than a failure.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from vinci.dossier.ciq import clean_num

#: A tranche whose `floating_rate` cell is any of these is FIXED. Anything else is floating — the
#: default leans to "floating" because mistaking a floating tranche for fixed puts a fabricated
#: coupon INTO the average, while the reverse only shrinks its coverage, which is reported.
_NOT_FLOATING = {"", "na", "n/a", "-", "–", "none", "no", "false", "fixed"}


class BorrowingUnavailableError(RuntimeError):
    """No tranche states both a principal and a fixed coupon, so there is no average to strike."""


@dataclass(frozen=True)
class Borrowing:
    """The cost of borrowing, with its own coverage stated beside it."""

    weighted_avg_coupon_pct: float
    #: Principal the average actually covers, and the total it was drawn from — the honest
    #: denominator. A 4.5% average over 30% of the stack is a different claim from one over 95%.
    covered_musd: float
    total_musd: float
    floating_musd: float
    #: ALL-IN, a SECOND BASIS and labelled as one. Eight floating tranches in the corpus state a
    #: current EFFECTIVE rate beside their benchmark ("SOFR + 3.500%" → 7.160%), so what a name pays
    #: TODAY is strikeable over far more of the stack than the fixed coupons alone: WERN's
    #: fixed-only average covers 5% of its principal and its all-in rate covers ~100%. Neither
    #: figure is the whole answer — the fixed average is CONTRACTED and will not move; the all-in is
    #: what is PAID and resets. Both are reported, each naming its basis, because the repo has
    #: already shipped one defect from two same-looking rows on different bases in one table.
    all_in_rate_pct: float | None
    all_in_covered_musd: float
    n_covered: int
    n_total: int
    source_ref: str

    @property
    def all_in_coverage(self) -> float:
        """Share of principal the all-in rate covers — typically far higher than `coverage`."""
        return self.all_in_covered_musd / self.total_musd if self.total_musd else 0.0

    @property
    def coverage(self) -> float:
        """Share of total principal the weighted average is struck over."""
        return self.covered_musd / self.total_musd if self.total_musd else 0.0

    @property
    def floating_share(self) -> float:
        return self.floating_musd / self.total_musd if self.total_musd else 0.0


def _is_floating(row: dict[str, Any]) -> bool:
    cell = str(row.get("floating_rate") or "").strip().lower()
    return cell not in _NOT_FLOATING


def borrowing(instruments: Any, *, source_ref: str) -> Borrowing:
    """Weighted-average coupon over tranches that state BOTH a principal and a fixed coupon.

    Raises rather than returning a zero: a name with debt it cannot price is a refusal the panel
    must render loudly, not a 0.0% that reads as free money.
    """
    if not isinstance(instruments, list) or not instruments:
        raise BorrowingUnavailableError(
            "the capital-structure panel lists no instruments, so there is no debt to price")
    total = 0.0
    floating = 0.0
    num = 0.0
    covered = 0.0
    all_in_num = 0.0
    all_in_covered = 0.0
    n_covered = 0
    for row in instruments:
        if not isinstance(row, dict):
            continue
        principal = clean_num(row.get("principal_musd"))
        if principal is None or principal <= 0:
            # A tranche with no stated principal cannot be weighted. It is excluded from BOTH the
            # numerator and the denominator rather than counted as zero — otherwise coverage would
            # read as complete while the stack it describes is not.
            continue
        total += principal
        rate = clean_num(row.get("coupon"))
        if rate is not None:
            # ALL-IN takes every tranche that states a rate, floating included at its current
            # effective rate. This is the only place a floating tranche contributes to a rate.
            all_in_num += principal * rate
            all_in_covered += principal
        if _is_floating(row):
            # ...and it contributes to NO fixed-coupon average. Averaging a resettable rate into the
            # contracted one conflates two bases; omitting the guard left eight corpus tranches
            # silently inside the fixed figure, and a fixture whose floating row had no coupon could
            # not see it.
            floating += principal
            continue
        if rate is None:
            continue
        num += principal * rate
        covered += principal
        n_covered += 1
    if not covered:
        raise BorrowingUnavailableError(
            f"no tranche states both a principal and a fixed coupon "
            f"({len(instruments)} instrument(s), {total:,.0f}musd principal, of which "
            f"{floating:,.0f}musd floating) — a weighted average struck here would be a number "
            f"about nothing")
    return Borrowing(
        weighted_avg_coupon_pct=num / covered,
        all_in_rate_pct=(all_in_num / all_in_covered) if all_in_covered else None,
        all_in_covered_musd=all_in_covered,
        covered_musd=covered, total_musd=total, floating_musd=floating,
        n_covered=n_covered, n_total=len(instruments), source_ref=source_ref,
    )
