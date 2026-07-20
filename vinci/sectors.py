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

from vinci.sic_table import SIC_TABLE


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


def _display_title(official: str) -> str:
    """Deterministic display casing over a VERBATIM official SEC title (stored ALL-CAPS).

    Word-wise capitalization; glue words stay lowercase except at the start of the title or of a
    parenthesised/hyphenated segment ("TRUCKING (NO LOCAL)" → "Trucking (No Local)",
    "SERVICES-PREPACKAGED SOFTWARE" → "Services-Prepackaged Software"). Pure presentation — the
    vendored table keeps the SEC's verbatim strings."""
    glue = {"and", "of", "or", "the", "a", "an", "etc.", "etc"}
    acronyms = {"nec": "NEC", "nec.": "NEC."}   # SIC "Not Elsewhere Classified" — never "Nec"

    def cap_word(w: str, first: bool) -> str:
        parts = w.split("-")
        out = []
        for i, part in enumerate(parts):
            low = part.lower()
            lead = low.lstrip("(")
            prefix = part[: len(part) - len(lead)].lower() if lead != low else ""
            if not lead:
                out.append(low)
                continue
            seg_first = first or i > 0 or prefix != ""
            if lead.rstrip(",") in acronyms or lead in acronyms:
                out.append(prefix + acronyms.get(lead, acronyms[lead.rstrip(",")] + ","))
                continue
            out.append(prefix + (lead.capitalize() if seg_first or lead not in glue else lead))
        return "-".join(out)

    words = official.split(" ")
    return " ".join(cap_word(w, i == 0) for i, w in enumerate(words))


def industry_for_sic(sic: str | int | None) -> str:
    """Map an SEC SIC code to its OFFICIAL industry title (display-cased) — finer than
    :func:`sector_for_sic`.

    The naming source is the vendored official SEC SIC code list (``vinci.sic_table.SIC_TABLE`` —
    the repo's ONE universe-wide fine-industry table; it replaced both the old hand-rolled
    ~80-bucket map here and the frontend ``_SIC_NAME`` map). Same discipline: DETERMINISTIC,
    STABLE, fail-honest (blank/non-numeric → ``"Unknown"``). A code the official table lacks
    FALLS BACK to the coarse sector, so an industry label is never *less* informative than the
    sector. This is a human-readable classification lens for the cross-sectional cluster read —
    NOT a peer cohort, NOT a driver/theme (that is the theme edge), and NEVER a
    screen / rank / verdict input.
    """
    if sic is None:
        return "Unknown"
    s = str(sic).strip()
    if not s.isdigit():
        return "Unknown"
    official = SIC_TABLE.get(s.zfill(4))
    if official:
        return _display_title(official)
    # no official entry → the coarse sector (never LESS informative than sector_for_sic)
    return sector_for_sic(sic)
