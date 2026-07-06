"""SIC → sector mapping — a derived view of the EDGAR SIC the resolver already provides.

This introduces NO new data source: the SIC code is the existing operating-co classification
(``resolver.sic_for`` / the universe gate). It maps that code to a coarse GICS-like sector so a
verdict can be sector-tagged at log time and the BUY−AVOID spread later read PER-SECTOR (a sector
with a positive spread = the discriminator's expertise is real there; poor/noisy = learn it or
filter it — see STATE.md §sector-expertise scoping).

The bucketing is deliberately coarse (~11 sectors) and refine-able; what matters is that it is
DETERMINISTIC and STABLE, so the per-sector grouping is consistent across verdicts. A blank/unknown
SIC fails honest → ``"Unknown"`` (never guessed).
"""

from __future__ import annotations


def sector_for_sic(sic: str | int | None) -> str:
    """Map an SEC SIC code to a coarse GICS-like sector. ``None``/blank/non-numeric → ``"Unknown"``.

    Ordered most-specific-first: a few 4-digit refinements (pharma, medical devices, REIT) override
    the 2-digit major-group rules, because those major groups (28 chemicals, 38 instruments, 67
    holding cos) otherwise mix sectors.
    """
    if sic is None:
        return "Unknown"
    s = str(sic).strip()
    if not s.isdigit():
        return "Unknown"
    n = int(s)
    mg = n // 100  # 2-digit major group, e.g. 7372 → 73

    # --- 4-digit refinements (override the major-group rules below) ---
    if 2833 <= n <= 2836:
        return "Health Care"  # pharmaceutical / biological products
    if n in (3826, 3827, 3829, 3841, 3842, 3843, 3844, 3845, 3851):
        return "Health Care"  # medical / analytical instruments & devices
    if n == 6798:
        return "Real Estate"  # REIT (sits inside the 67 holding/investment major group)

    # --- 2-digit major groups ---
    if mg == 73 or mg in (35, 36):
        return "Technology"  # business/software services; computers & electronics
    if mg == 80:
        return "Health Care"  # health services
    if mg == 65 or mg == 66:
        return "Real Estate"
    if mg in (60, 61, 62, 63, 64, 67):
        return "Financials"  # banks, credit, insurance, holding/investment
    if mg in (13, 29):
        return "Energy"  # oil & gas extraction; petroleum refining
    if mg in (10, 12, 14, 28, 26, 32, 33):
        return "Materials"  # mining, chemicals, paper, stone/clay/glass, primary metals
    if mg == 48:
        return "Communication Services"
    if mg == 49:
        return "Utilities"
    if mg in (1, 2, 7, 9, 20, 21, 54):
        return "Consumer Staples"  # agriculture, food, tobacco, food stores
    if (52 <= mg <= 59) or mg in (22, 23, 25, 30, 31, 78, 79):
        return "Consumer Discretionary"  # retail, apparel, autos-as-sold, entertainment
    if (15 <= mg <= 17) or (34 <= mg <= 39) or (mg == 37) or (40 <= mg <= 47) or mg in (50, 51):
        return "Industrials"  # construction, machinery, transport equip, transportation, wholesale
    return "Other"


def industry_for_sic(sic: str | int | None) -> str:
    """Map an SEC SIC code to a READABLE sub-industry — finer than :func:`sector_for_sic`.

    Same discipline: DETERMINISTIC, STABLE, fail-honest (blank/non-numeric → ``"Unknown"``). Where a
    code has no specific sub-industry it FALLS BACK to the coarse sector, so an industry label is
    never *less* informative than the sector. This is a human-readable classification lens for the
    cross-sectional cluster read — NOT a peer cohort, NOT a driver/theme (that is the theme edge),
    and NEVER a screen / rank / verdict input.
    """
    if sic is None:
        return "Unknown"
    s = str(sic).strip()
    if not s.isdigit():
        return "Unknown"
    n = int(s)
    mg = n // 100  # 2-digit major group

    # --- Health Care ---
    if 2833 <= n <= 2834:
        return "Pharma"
    if n == 2835:
        return "Diagnostics"
    if n == 2836:
        return "Biotech"
    if n in (3826, 3827, 3829):
        return "Life Sciences Tools"
    if 3840 <= n <= 3851:
        return "Medical Devices"
    if 8060 <= n <= 8069:
        return "Hospitals"
    if 8050 <= n <= 8059:
        return "Healthcare Facilities"
    if n == 8071:
        return "Diagnostics"
    if mg == 80:
        return "Healthcare Services"
    if n == 6324:
        return "Managed Care"

    # --- Technology ---
    if n == 7372:
        return "Software"
    if n in (7370, 7371, 7373, 7374, 7379):
        return "IT Services"
    if n == 3674:
        return "Semiconductors"
    if n == 3559:
        return "Semi Equipment"
    if n == 3576:
        return "Networking"
    if n in (3571, 3572, 3575, 3577, 3578):
        return "Computer Hardware"
    if n in (3661, 3663, 3669):
        return "Comms Equipment"
    if 3670 <= n <= 3679:
        return "Electronic Components"

    # --- Financials ---
    if 6020 <= n <= 6036:
        return "Banks"
    if n == 6141:
        return "Consumer Finance"
    if n in (6153, 6159, 6172):
        return "Commercial Finance"
    if n in (6200, 6211):
        return "Capital Markets"
    if n == 6282:
        return "Asset Management"
    if n in (6311, 6321, 6331, 6411):
        return "Insurance"

    # --- Real Estate ---
    if n == 6798:
        return "REIT"
    if n == 6500 or 6510 <= n <= 6519:
        return "Real Estate"
    if n == 6531:
        return "Real Estate Services"

    # --- Energy ---
    if n == 1311:
        return "Oil & Gas E&P"
    if n in (1381, 1389, 3533):
        return "Oil & Gas Services"
    if n == 2911:
        return "Refining"

    # --- Materials ---
    if n == 1040:
        return "Gold Mining"
    if 1000 <= n <= 1099 or 1400 <= n <= 1499:
        return "Metals & Mining"
    if 3310 <= n <= 3316:
        return "Steel"
    if 2600 <= n <= 2679:
        return "Paper & Packaging"
    if n in (3241, 3270, 3272, 3281):
        return "Building Materials"
    if 2800 <= n <= 2899:
        return "Chemicals"

    # --- Industrials ---
    if 3720 <= n <= 3728 or n in (3760, 3480, 3812):
        return "Aerospace & Defense"
    if n == 4011 or n == 4013:
        return "Rail"
    if 4200 <= n <= 4231:
        return "Trucking & Logistics"
    if 4500 <= n <= 4581:
        return "Airlines"
    if 4700 <= n <= 4789:
        return "Transport Services"
    if 1600 <= n <= 1799:
        return "Construction"
    if 3500 <= n <= 3569:
        return "Machinery"
    if 5000 <= n <= 5199:
        return "Distributors"

    # --- Consumer Discretionary ---
    if n in (3711, 3713, 3714, 3715):
        return "Autos & Parts"
    if 2300 <= n <= 2399 or 3100 <= n <= 3199:
        return "Apparel & Footwear"
    if n == 5812:
        return "Restaurants"
    if 7000 <= n <= 7011:
        return "Hotels & Leisure"
    if n in (7812, 7822, 7900, 7990, 7997):
        return "Media & Entertainment"
    if n in (1531, 1520, 1522, 2450):
        return "Homebuilding"
    if 5200 <= n <= 5999:
        return "Retail"

    # --- Consumer Staples ---
    if 2080 <= n <= 2086:
        return "Beverages"
    if n == 2100 or 2110 <= n <= 2141:
        return "Tobacco"
    if n in (2840, 2842, 2844):
        return "Household Products"
    if 2000 <= n <= 2099:
        return "Food Products"
    if 100 <= n <= 999:
        return "Agriculture"

    # --- Communication Services ---
    if n == 4813:
        return "Telecom"
    if n == 4812:
        return "Wireless Telecom"
    if n == 4841:
        return "Cable & Satellite"
    if n in (4832, 4833):
        return "Broadcasting"
    if n == 4899:
        return "Media & Internet"
    if n == 2711:
        return "Publishing"

    # --- Utilities ---
    if n == 4911 or n == 4931:
        return "Electric Utilities"
    if n in (4922, 4923, 4924, 4925):
        return "Gas Utilities"
    if n == 4941:
        return "Water Utilities"
    if n == 4991:
        return "Renewables & IPPs"

    # no specific sub-industry → the coarse sector (never LESS informative than sector_for_sic)
    return sector_for_sic(sic)
