"""Deterministic classification of workbook rows — role, direction, listing — by EXACT-STRING table.

Every table below is keyed on the workbook's own verbatim text. An unseen string RAISES: a new
role phrase is a human's call to classify, never a regex's guess. The workbook text is always
carried beside the derived class, so the audit class can be checked against what was written.

THE RULE THIS ENCODES (operator brief §1): a company MENTION is not a recommendation. Only a
stated analyst rating is directional, and only ``Overweight`` is scored as a long investment.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Role(StrEnum):
    RECOMMENDATION = "ACTUAL_RECOMMENDATION"  # a stated analyst rating (OW / EW / UW)
    THEMATIC_BENEFICIARY = "THEMATIC_BENEFICIARY"
    RISK = "RISK"
    CONTEXTUAL = "CONTEXTUAL"


class Direction(StrEnum):
    LONG = "LONG"  # Overweight — the only class scored as a long investment
    NEUTRAL = "NEUTRAL"  # Equal-Weight — reported separately, never in a long hit-rate
    UNDERWEIGHT = "UNDERWEIGHT"  # reported separately; NOT scored as a short (Thesis Signals row 9)
    NONDIRECTIONAL = "NONDIRECTIONAL"  # no rating stated — no return is computed


#: Workbook 'Exact role in thesis' → audit role. Verbatim keys; an unseen phrase raises.
ROLE_TABLE: dict[str, Role] = {
    "AI adopter + existing Overweight stock rating": Role.RECOMMENDATION,
    "High-pricing-power AI adopter + existing Overweight stock rating": Role.RECOMMENDATION,
    "AI materiality raised to core thesis + stock rating Overweight": Role.RECOMMENDATION,
    "AI materiality raised to core thesis + stock rating Equal-Weight": Role.RECOMMENDATION,
    "AI materiality raised to core thesis + stock rating Underweight": Role.RECOMMENDATION,
    "Named in AI-agent infrastructure/vendor mapping (not itself an explicit buy)":
        Role.THEMATIC_BENEFICIARY,
    "Foundry leader / potential beneficiary": Role.THEMATIC_BENEFICIARY,
    "Foundry / CHIPS Act potential beneficiary": Role.THEMATIC_BENEFICIARY,
    "Foundry contender facing obstacles": Role.RISK,
    "Industry context / IDM": Role.CONTEXTUAL,
    "Fabless industry example": Role.CONTEXTUAL,
    "Sanctions historical example": Role.CONTEXTUAL,
    "Search / discovery market example and antitrust case": Role.CONTEXTUAL,
    "Data source for social-commerce survey": Role.CONTEXTUAL,
    "Regulatory example re FTC consent order": Role.CONTEXTUAL,
    "Concentration / Magnificent Seven comparator; NOT long recommendation": Role.CONTEXTUAL,
    "Private AI model provider used as thematic context": Role.CONTEXTUAL,
}

#: Workbook 'Actual research rating' → direction. Verbatim keys; an unseen rating raises.
RATING_TABLE: dict[str, Direction] = {
    "Overweight": Direction.LONG,
    "Equal-Weight": Direction.NEUTRAL,
    "Underweight": Direction.UNDERWEIGHT,
    "Not stated": Direction.NONDIRECTIONAL,
}

#: (Publication ID, exhibit, rating) → the workbook's own Thesis Signals ID. Only the pairs the
#: 'Thesis Signals' sheet itself defines; Exhibit 79 Equal-Weight names have NO workbook signal
#: ("Equal/Underweight names not a long signal") and stay unmapped rather than given an invented id.
SIGNAL_TABLE: dict[tuple[str, str, str], str] = {
    ("MS-01", "Exhibit 55", "Overweight"): "MS24_ADOPTER_OW",
    ("MS-02", "Exhibit 32", "Overweight"): "MS24_JUNE_PP",
    ("MS-03", "Exhibit 79", "Overweight"): "MS25_UPGRADE_OW",
    ("MS-03", "Exhibit 79", "Underweight"): "MS25_UPGRADE_UW",
}


class UnclassifiedError(ValueError):
    """A workbook string the tables do not know — a human must classify it."""


def role_of(role_text: str) -> Role:
    try:
        return ROLE_TABLE[role_text]
    except KeyError:
        raise UnclassifiedError(f"unclassified role text {role_text!r} — add it to ROLE_TABLE "
                                f"deliberately; never infer a role") from None


def direction_of(rating_text: str) -> Direction:
    try:
        return RATING_TABLE[rating_text]
    except KeyError:
        raise UnclassifiedError(f"unclassified rating {rating_text!r} — add it to RATING_TABLE "
                                f"deliberately") from None


def signal_id_of(pub_id: str, place: str, rating: str) -> str:
    """The workbook Thesis-Signals id this rated row belongs to, or ``""`` when none is defined."""
    exhibit = place.split(",")[0].strip()
    return SIGNAL_TABLE.get((pub_id, exhibit, rating), "")


# --- listings ---------------------------------------------------------------------------------

class Availability(StrEnum):
    POLYGON_CANDIDATE = "POLYGON_CANDIDATE"  # US-listed symbol; identity still to be verified
    UNAVAILABLE_POLYGON = "UNAVAILABLE_POLYGON"  # non-US primary listing — Polygon has no feed
    NOT_LISTED = "NOT_LISTED"  # private company


@dataclass(frozen=True)
class Listing:
    audit_ticker: str
    availability: Availability
    exchange_mic: str
    currency: str
    country: str


#: Exchange suffix on the workbook ticker → (MIC, listing currency, country). Polygon's stock
#: markets are US exchanges + US OTC only (probed 2026-10-09: `market` ∈ {stocks, otc}); none of
#: these primary venues is carried, so every suffixed ticker is UNAVAILABLE_POLYGON.
SUFFIX_TABLE: dict[str, tuple[str, str, str]] = {
    ".L": ("XLON", "GBP", "United Kingdom"),
    ".T": ("XTKS", "JPY", "Japan"),
    ".KS": ("XKRX", "KRW", "South Korea"),
    ".DE": ("XETR", "EUR", "Germany"),
    ".AS": ("XAMS", "EUR", "Netherlands"),
    ".AX": ("XASX", "AUD", "Australia"),
    ".TO": ("XTSE", "CAD", "Canada"),
    ".TW": ("XTAI", "TWD", "Taiwan"),
    ".SZ": ("XSHE", "CNY", "China"),
    ".SS": ("XSHG", "CNY", "China"),
    ".HK": ("XHKG", "HKD", "Hong Kong"),
}

NOT_LISTED_TEXT = "Private / not listed"


def listing_of(audit_ticker: str) -> Listing:
    if audit_ticker == NOT_LISTED_TEXT:
        return Listing(audit_ticker, Availability.NOT_LISTED, "", "", "")
    for suffix, (mic, ccy, country) in SUFFIX_TABLE.items():
        if audit_ticker.endswith(suffix):
            return Listing(audit_ticker, Availability.UNAVAILABLE_POLYGON, mic, ccy, country)
    if "." in audit_ticker or not audit_ticker.replace("-", "").isalnum():
        raise UnclassifiedError(f"unrecognised listing suffix on {audit_ticker!r}")
    return Listing(audit_ticker, Availability.POLYGON_CANDIDATE, "", "USD", "United States")
