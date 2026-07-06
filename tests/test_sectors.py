"""SIC → coarse sector mapping — deterministic, fail-honest (blank/None → 'Unknown', never guessed).

The sector is a DERIVED view of the EDGAR SIC the resolver already provides — never a new data
source, never a screen/rank/verdict input. These pins lock the coarse buckets used by the Overshoot
cluster roll-up and the ledger's per-sector spread read.
"""

from __future__ import annotations

from vinci.sectors import industry_for_sic, sector_for_sic


def test_sector_for_sic_coarse_buckets() -> None:
    assert sector_for_sic("7372") == "Technology"   # prepackaged software (major group 73)
    assert sector_for_sic("2834") == "Health Care"  # pharma 4-digit refinement overrides mg 28
    assert sector_for_sic("6798") == "Real Estate"  # REIT refinement inside the 67 holding group
    assert sector_for_sic("1311") == "Energy"       # crude petroleum & natural gas (mg 13)
    assert sector_for_sic(7372) == "Technology"     # accepts an int SIC too


def test_sector_for_sic_fails_honest_never_guesses() -> None:
    # blank / None / non-numeric → 'Unknown' (matches the universe gate's fail-CLOSED treatment)
    assert sector_for_sic(None) == "Unknown"
    assert sector_for_sic("") == "Unknown"
    assert sector_for_sic("   ") == "Unknown"
    assert sector_for_sic("N/A") == "Unknown"


def test_industry_for_sic_finer_sub_industries() -> None:
    # the finer lens bifurcates what the coarse sector lumps
    assert industry_for_sic("7372") == "Software"        # not just "Technology"
    assert industry_for_sic("3674") == "Semiconductors"  # ...same sector, different driver
    assert industry_for_sic("2836") == "Biotech"         # Health Care → biotech
    assert industry_for_sic("2834") == "Pharma"          # Health Care → pharma
    assert industry_for_sic("8062") == "Hospitals"       # Health Care → hospitals
    assert industry_for_sic("6798") == "REIT"


def test_industry_for_sic_falls_back_to_sector_never_less_informative() -> None:
    # an unmapped code is never worse than the coarse sector; blank stays 'Unknown'
    assert industry_for_sic("3690") == sector_for_sic("3690") == "Technology"  # unmapped tech code
    assert industry_for_sic("9995") == "Other"
    assert industry_for_sic(None) == "Unknown"
    assert industry_for_sic("") == "Unknown"
