"""IMPLIED RENT PER MW PER YEAR — the instrument the ai-compute-platform card left behind.

WHY IT OUTLIVES THE CARD. The `ai-compute-platform` thesis was recorded FALSIFIED pre-declaration
(`docs/records/2026-09-02-orcl-ruled-inside-the-scaled-cloud-boundary.md`). Its central claim was
that holders of energized, grid-interconnected sites own a scarce asset the market misprices as
mining property. The direct test of scarcity is whether realized lease pricing RISES: an owner of a
scarce appreciating asset earns more per MW over time. It did not — APLD's five leases price flat.

A killed card that leaves a standing trigger is worth more than a declared one with the evidence
against it. If implied $/MW/yr starts rising ACROSS ISSUERS, the thesis reanimates on evidence and
the instrument already exists.

WHAT IT REFUSES. It computes and never concludes. It also refuses to compare across issuers whose
contract value is composed differently: CORZ's leases are triple-net with "pass-through provisions
that allow us to recover the cost of customer power usage", so its revenue per MW includes power
that another issuer's may exclude. Comparability is asserted by the caller, never assumed here.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LeaseRent:
    """One disclosed lease reduced to $/MW/yr. Every field comes from the issuer's own filing."""

    issuer: str
    lease: str
    signed: str | None          # None = the filing gives no signing date (excluded from any trend)
    mw: float
    contract_value_usd_m: float
    term_years: float
    counterparty: str
    credit: str                 # disclosed credit character — the key confounder

    @property
    def usd_m_per_mw_year(self) -> float:
        return self.contract_value_usd_m / self.mw / self.term_years


# APLD is the ONLY issuer in the tier disclosing contract value, MW and term per lease. These five
# reconcile exactly to its $36.2bn / 1,410 MW headline, which is the check that the reduction is
# faithful rather than assembled. WULF and RIOT disclose MW and term but no contract value; CORZ
# discloses neither (verified against its full FY2025 10-K, not an excerpt: no "total contract
# value", no "contracted revenue", no RPO, no per-kW/MW figure).
APLD_LEASES: tuple[LeaseRent, ...] = (
    LeaseRent("APLD", "CoreWeave ELN-02/03 + Building 4", "2025-08-28", 400, 11_000, 15,
              "CoreWeave", "non-IG"),
    LeaseRent("APLD", "Polaris Forge 2", "2025-10-22", 200, 5_000, 15,
              "US investment-grade hyperscaler", "IG"),
    LeaseRent("APLD", "Delta Forge 1", "2026-04-23", 300, 7_500, 15,
              "US investment-grade hyperscaler", "IG"),
    LeaseRent("APLD", "Polaris Forge 3", None, 300, 7_500, 15,
              "high investment-grade hyperscaler", "IG"),
    LeaseRent("APLD", "Delta Forge 2", None, 210, 5_200, 15,
              "high investment-grade hyperscaler", "IG"),
)


def credit_clean_series(leases: tuple[LeaseRent, ...]) -> list[LeaseRent]:
    """Dated leases of ONE credit character, oldest first — the only trend that is not confounded.

    TENANT CREDIT IS THE CONFOUNDER, not a detail. A weaker tenant pays more rent for the same
    megawatt, so a series mixing credit qualities reads as a price trend when it is a credit spread:
    including APLD's non-IG CoreWeave lease turns a flat series into -9.1%, and the -9.1% is almost
    entirely that one anchor. Undated leases are excluded because a trend needs an order.
    """
    dated = [x for x in leases if x.signed is not None and x.credit == "IG"]
    return sorted(dated, key=lambda x: x.signed or "")


def range_pct(leases: list[LeaseRent]) -> float | None:
    """First-to-last change in $/MW/yr, or None if fewer than two points."""
    if len(leases) < 2:
        return None
    return leases[-1].usd_m_per_mw_year / leases[0].usd_m_per_mw_year - 1.0


# The standing trigger. NOT a falsifier on a dead card — an instrument that reanimates
# a killed thesis if the world changes, stated so it cannot be quietly re-tuned later.
REANIMATION_TRIGGER = (
    "Implied $/MW/yr RISES across two or more credit-comparable leases signed at least two "
    "quarters apart, at ANY issuer in the powered-infrastructure population, or a SECOND "
    "issuer begins disclosing contract value with MW and term (which would make the series "
    "cross-issuer for the first time). Either event reopens `ai-compute-platform`, which was "
    "falsified pre-declaration on a flat single-issuer series."
)
