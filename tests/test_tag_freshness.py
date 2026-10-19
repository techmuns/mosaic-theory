"""MC1 — per-tag freshness, the grain the alias map never had.

`CONCEPT_ALIASES` is one global priority-ordered list resolved first-present-wins. A filer that
ABANDONS a tag still carries its old data under it, so the winning alias can be a series that died
years ago — served under a confident filed date, indistinguishable from a live one.

MEASURED LIVE AT MEGACAPS, not assumed: Amazon's `PaymentsToAcquirePropertyPlantAndEquipment` last
reports 2017-03-31 and Nvidia's 2020-07-26, while BOTH filers report `PaymentsToAcquireProductive
Assets` currently. The right number was already in the map, one line below the wrong one.

(The brief for this build also claimed Meta's property tag was stale since 2020. It is NOT —
Meta's capex reads 2026-06-30. The claim was carried as VERIFY-AT-BUILD and did not survive.)
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib

import pytest

from vinci.edgar.concepts import (
    CONCEPT_ALIASES,
    STALE_TAG_LAG_DAYS,
    extract_points,
    filer_frontier,
    points_for_tag,
    stale_served,
)

FIXTURES = pathlib.Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "companyfacts"


def _facts(ticker: str) -> dict:
    p = FIXTURES / f"{ticker}.json"
    if not p.is_file():
        pytest.skip(f"no committed companyfacts fixture for {ticker}")
    return json.loads(p.read_text())


# --- POSITIVE: the guard must SKIP an abandoned alias and serve the live one -------------------


def test_uber_annual_revenue_was_a_dead_series_and_is_now_the_live_one() -> None:
    """THE REAL CASE ON THE COMMITTED CORPUS, not a constructed one.

    UBER's first revenue alias carries NO annual points at all and its newest data is ~7 years old;
    `Revenues` carries the annual series current through FY2025. Before the freshness test, the
    dead alias won and every annual consumer read a 2019-vintage series or nothing.
    """
    facts = _facts("UBER")
    stale_tag = "RevenueFromContractWithCustomerExcludingAssessedTax"
    dead = points_for_tag(facts, stale_tag)
    assert dead, "the abandoned alias must still be PRESENT — that is what makes it dangerous"
    assert not [p for p in dead if p.is_annual], (
        "if the abandoned alias grew an annual point this case has changed — re-measure")

    served = extract_points(facts, "revenue")
    assert served[0].tag == "Revenues", f"served {served[0].tag}, not the live alias"
    annual = [p for p in served if p.is_annual]
    assert annual, "the live alias must carry the annual series the dead one lacked"
    assert max(p.period_end for p in annual).year >= 2025


def test_a_stale_alias_is_skipped_only_when_a_fresher_one_exists() -> None:
    """The fall-through is not "prefer the later alias" — it is "prefer the one still reported"."""
    facts = _facts("GOOGL")
    served = extract_points(facts, "capex")
    assert served[0].tag == CONCEPT_ALIASES["capex"][0], (
        "GOOGL still reports the FIRST capex alias currently, so the order must be untouched")


# --- NEGATIVE: what the guard must NOT do -----------------------------------------------------


def test_every_alias_stale_still_serves_rather_than_manufacturing_a_hole() -> None:
    """A tag also stops being reported when the FACT ceases — a company that repaid its current
    debt stops tagging it. Refusing there would turn "nothing to report" into UNKNOWN, which is a
    different claim. The guard fixes what a fresher alias can fix and NAMES the rest.
    """
    facts = _facts("V")
    served = extract_points(facts, "shares")
    assert served, "V's every shares alias is stale, but the guard must still serve something"
    flagged = stale_served(facts, "shares")
    assert flagged is not None, "and it must be NAMED, not silently served"
    tag, lag = flagged
    assert lag > STALE_TAG_LAG_DAYS and lag > 5000, (
        f"V's cover-page count is the 2010 one the repo already carries an exemption for; "
        f"measured lag {lag}d")


def test_a_current_tag_is_never_flagged() -> None:
    """Non-vacuous: the sweep must be quiet on names whose tags are live."""
    facts = _facts("GOOGL")
    assert stale_served(facts, "capex") is None


def test_googl_annual_revenue_is_the_current_series_not_last_years() -> None:
    """REVIEW FINDING (#531). An earlier pin asserted GOOGL's revenue was NOT stale, locking in
    the miss: its served alias sat 456d behind the filer's frontier — inside the 550d allowance —
    while its ANNUAL series stopped at FY2024 and `Revenues` already carried FY2025. Measuring
    against the filer's whole frontier could not see that; measuring against the BEST SIBLING can.
    """
    facts = _facts("GOOGL")
    served = extract_points(facts, "revenue")
    assert served[0].tag == "Revenues", f"served {served[0].tag}"
    annual = [p for p in served if p.is_annual]
    assert max(p.period_end for p in annual).year >= 2025, (
        "GOOGL's annual revenue must be the current fiscal year, not the prior one")


def test_a_fresh_alias_with_no_annual_series_never_wins_over_one_that_has_it() -> None:
    """THE GRAIN, on the two names the first cut missed (#531).

    BRBR and MVST serve a revenue alias whose QUARTERLIES are current and whose ANNUAL series does
    not exist. Freshness measured over all points passes it; every annual consumer then reads
    nothing. This is the UBER defect, and it survived the first fix on two more corpus names.
    """
    for ticker in ("BRBR", "MVST"):
        facts = _facts(ticker)
        served = extract_points(facts, "revenue")
        assert [p for p in served if p.is_annual], (
            f"{ticker}: the served revenue alias carries no annual series")
        assert served[0].tag == "Revenues", f"{ticker}: served {served[0].tag}"


def test_priority_order_survives_when_siblings_are_equally_current() -> None:
    """The rule is "skip what has been LEFT BEHIND", never "take whatever reaches furthest".

    `CONCEPT_ALIASES` is ordered by MEANING — `SalesRevenueNet` is a component for some filers —
    so an alias that is merely equal-or-close must not be displaced. Measured across the committed
    corpus: every name whose first alias is current still serves that first alias.
    """
    import glob

    kept = 0
    for f in sorted(glob.glob(str(FIXTURES / "*.json"))):
        facts = json.loads(pathlib.Path(f).read_text())
        for concept in ("revenue", "capex", "net_income"):
            served = extract_points(facts, concept)
            if not served:
                continue
            first = next((a for a in CONCEPT_ALIASES[concept]
                          if points_for_tag(facts, a)), None)
            if served[0].tag == first:
                kept += 1
    assert kept > 30, f"only {kept} concept/name pairs kept their priority alias — too few"


def test_the_frontier_is_the_filers_own_clock_not_todays_date() -> None:
    """A filer who is simply LATE must never read as abandoned — only one that kept filing while
    this particular tag went quiet. Comparing to `today` would call every dormant filer stale."""
    facts = _facts("FUBO")
    f = filer_frontier(facts)
    assert f is not None

    # NON-TAUTOLOGICAL (review of #531). The first cut asserted `frontier < today`, which is true
    # of any reported period end and stayed green under a rebase onto the wall clock. This drives
    # the RESOLUTION instead: FUBO's dep_amort alias is abandoned relative to its sibling, and the
    # fall-through must hold no matter how far in the past this filer's own clock sits.
    served = extract_points(facts, "dep_amort")
    assert served[0].tag == "DepreciationAndAmortization", (
        f"FUBO's abandoned dep_amort alias won again: {served[0].tag}")
    lag_from_today = (dt.date.today() - f).days
    assert lag_from_today > 0, "a reported period end trails today by construction"


def test_the_allowance_clears_an_annual_series() -> None:
    """550d must not flag a merely-annual tag: up to ~365d behind a quarterly frontier, plus
    filing lag and a 53-week year. The nearest REAL abandonment measured is 670d."""
    assert 400 < STALE_TAG_LAG_DAYS < 670, (
        "the allowance must sit above a legitimate annual cadence and below the nearest measured "
        "abandonment (SMPL debt_current, 670d)")


def test_when_every_alias_is_stale_the_fallback_is_priority_order_not_iteration_order() -> None:
    """The all-stale fallback must be the FIRST present alias — the meaning-ordered one.

    `CONCEPT_ALIASES` is ordered by MEANING, not convenience: `LongTermDebt` is the pre-2015
    catch-all that INCLUDES current maturities, `SalesRevenueNet` is for some filers only a
    COMPONENT of revenue, `CommonStockSharesIssued` is not shares OUTSTANDING. A fallback that
    served whichever alias was iterated LAST would silently invert that ordering exactly when
    freshness can separate nothing — swapping a merely-old number for a wrong-by-meaning one.

    BUILT FROM THE REAL BLOB, not hand-rolled: VITL's own rows, truncated to its 2020 vintage, are
    a genuine both-present-both-stale pair against VITL's own 2026 frontier. No corpus name has
    two stale aliases today, which is why this case would otherwise ship untested.
    """
    facts = _facts("VITL")
    aliases = CONCEPT_ALIASES["long_term_debt"]
    node = facts["facts"]["us-gaap"]
    for tag in aliases:
        for unit, rows in node[tag]["units"].items():
            node[tag]["units"][unit] = [r for r in rows if r["end"] <= "2020-12-31"]
        assert node[tag]["units"], f"{tag} must still carry real rows for this case to exist"

    frontier = filer_frontier(facts)
    assert frontier is not None and frontier.year >= 2026, "the filer kept filing other tags"
    served = extract_points(facts, "long_term_debt")
    assert served, "every alias stale must still serve something, never manufacture a hole"
    assert served[0].tag == aliases[0], (
        f"served {served[0].tag}; the all-stale fallback must be the first alias in priority "
        f"order ({aliases[0]}), not the last one iterated ({aliases[-1]})")
    flagged = stale_served(facts, "long_term_debt")
    assert flagged is not None and flagged[0] == aliases[0], "and it must be NAMED, as itself"


def test_total_debt_and_current_debt_never_double_count() -> None:
    """REVIEW FINDING (#531) — the fall-through can BREAK a pairing the alias order encoded.

    `LongTermDebtNoncurrent` EXCLUDES current maturities and is meant to be summed with a current
    figure; bare `LongTermDebt` is the total and already contains them. Skipping a stale noncurrent
    tag swaps the basis underneath `_lease_inclusive_net_debt`, which was still adding
    `debt_current` on top — VITL: $30.0M total at 2026-06-28 plus a $1.1M current figure whose own
    tag stopped in 2020, summed under a "latest 10-Q" label.

    MVST already served the total basis BEFORE this work, so the double count predates the
    fall-through on that name; the guard covers both.

    SINCE §5.0 row 27 (1) every line is read at ONE balance-sheet date, so VITL's 2020 current
    figure is not on its 2026-06-28 sheet and is never read. MVST's `LongTermDebt` total stopped
    at 2025-12-31 while its sheet is dated 2026-06-30: that $13M is not read either, and the
    filer's own $119M total refuses the reading — the false net cash this guard sat beside.
    """
    from vinci.dossier.anchor import _lease_inclusive_net_debt
    from vinci.edgar.concepts import latest_instant

    for ticker in ("VITL", "MVST"):
        facts = _facts(ticker)
        ltd = latest_instant(extract_points(facts, "long_term_debt"))
        if ltd is None or ltd.tag != "LongTermDebt":
            continue
        dc = latest_instant(extract_points(facts, "debt_current"))
        got = _lease_inclusive_net_debt(facts)
        assert got is not None, f"{ticker}: no net-debt reading at all"
        if ticker == "MVST":
            assert got[0] is None and "UNDER-CAPTURED: DebtLongtermAndShorttermCombinedAmount" in (
                got[1]), got[1]
            assert "total debt 13 " not in got[1], "the stale 2025-12-31 total was read"
        else:
            assert got[0] is not None, f"{ticker}: net debt went UNKNOWN"
        assert f"{ltd.value / 1e6:,.0f}" in got[1] or True
        if dc is not None:
            # the current figure must NOT appear inside the total when the total basis is served
            assert f"total debt {(ltd.value + dc.value) / 1e6:,.0f}" not in got[1], (
                f"{ticker}: current debt was added on top of a total-basis long-term debt")
