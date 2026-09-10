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

LEASES ARE NOT BORROWINGS (review finding, PR #598). The CIQ capital panel lists operating- and
finance-lease liabilities as tranches typed 'Capital Lease', and their `coupon` cell is the
ASC-842 discount / incremental-borrowing rate the filer imputed — not a contracted coupon on
borrowed money. Averaging those in does not shade the figure, it REPLACES it: measured on the
committed corpus, the whole of SMPL's (6.00%), WERN's (4.70%), EPAM's (4.80%), VITL's and TECX's
"cost of borrowing" was lease discount rates and nothing else, and TECX — which has no borrowings
at all — reported 15.47%, the highest figure in the corpus, off a $0.4M finance lease and a $0.9M
operating lease. Lease principal is reported as its own field so nothing is deleted, and a name
whose only priced tranches are leases now REFUSES.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from vinci.dossier.ciq import clean_num

#: A tranche whose `floating_rate` cell is any of these is FIXED. Anything else is floating — the
#: default leans to "floating" because mistaking a floating tranche for fixed puts a fabricated
#: coupon INTO the average, while the reverse only shrinks its coverage, which is reported.
#: The empty string is CIQ's own "not floating" cell; an ABSENT or NULL field is a different
#: thing — extraction said nothing — and leans floating, per the sentence above. An earlier cut
#: collapsed the two with `str(row.get(...) or "")`, which made a failed extraction read as FIXED
#: and put a possibly-resettable coupon into the contracted average: the stated default, inverted.
_NOT_FLOATING = {"", "na", "n/a", "-", "–", "none", "no", "false", "fixed"}

#: CIQ's instrument `type` for lease liabilities — it covers BOTH operating and finance leases
#: (every one of the 24 lease rows in the committed corpus carries it, and no non-lease row does),
#: which is why the filter is on the structured type rather than a description regex.
_LEASE_TYPES = {"capital lease"}


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
    #: Lease-liability principal, held OUT of every figure above and reported here so the fact is
    #: not deleted. A reader who wants the lease-inclusive number can strike it; the panel will not
    #: strike it for them and call it a cost of borrowing.
    lease_musd: float
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
    raw = row.get("floating_rate")
    if raw is None:
        # ABSENT OR NULL IS NOT THE EMPTY CELL. Extraction said nothing about this tranche, and the
        # stated default leans FLOATING: mistaking a floating tranche for fixed puts a fabricated
        # coupon into the contracted average, while the reverse only shrinks coverage, which is
        # reported. `or ""` collapsed this case onto CIQ's explicit "not floating" cell.
        return True
    return str(raw).strip().lower() not in _NOT_FLOATING


def _is_lease(row: dict[str, Any]) -> bool:
    return str(row.get("type") or "").strip().lower() in _LEASE_TYPES


def borrowing(instruments: Any, *, source_ref: str) -> Borrowing:
    """Weighted-average coupon over tranches that state BOTH a principal and a fixed coupon.

    Raises rather than returning a zero: a name with debt it cannot price is a refusal the panel
    must render loudly, not a 0.0% that reads as free money.
    """
    if not isinstance(instruments, list):
        # LOUD, NOT A REFUSAL. The dossier holds the list inside a `{value, source_ref, status}`
        # envelope, so `cs["instruments"]` is the shape a caller most easily passes by mistake —
        # and the refusal branch would then state "this name has no debt to price" about a name
        # with a 19-tranche stack. A wiring bug must not be able to render as an answer.
        raise TypeError(
            f"borrowing() takes the instrument LIST, got {type(instruments).__name__} — pass "
            f"`capital_structure.instruments['value']`, not the fact envelope; a mis-wired call "
            f"must not be able to read as 'no debt'")
    if not instruments:
        raise BorrowingUnavailableError(
            "the capital-structure panel lists no instruments, so there is no debt to price")
    total = 0.0
    floating = 0.0
    lease = 0.0
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
        if _is_lease(row):
            # A lease liability is not borrowed money and its `coupon` is an imputed discount rate.
            # It is out of the numerator, the denominator and the floating share alike — reported on
            # its own field instead, so the fact survives without contaminating a cost of debt.
            lease += principal
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
            f"({len(instruments)} instrument(s), {total:,.0f}musd non-lease principal, of which "
            f"{floating:,.0f}musd floating; {lease:,.0f}musd of lease liabilities excluded as not "
            f"borrowed money) — a weighted average struck here would be a number about nothing")
    return Borrowing(
        weighted_avg_coupon_pct=num / covered,
        all_in_rate_pct=(all_in_num / all_in_covered) if all_in_covered else None,
        all_in_covered_musd=all_in_covered,
        covered_musd=covered, total_musd=total, floating_musd=floating, lease_musd=lease,
        n_covered=n_covered, n_total=len(instruments), source_ref=source_ref,
    )
