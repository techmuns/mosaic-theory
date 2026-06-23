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
