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
    assert stale_served(facts, "revenue") is None


def test_the_frontier_is_the_filers_own_clock_not_todays_date() -> None:
    """A filer who is simply LATE must never read as abandoned — only one that kept filing while
    this particular tag went quiet. Comparing to `today` would call every dormant filer stale."""
    facts = _facts("SMPL")
    f = filer_frontier(facts)
    assert f is not None and f < dt.date.today(), (
        "the frontier is a REPORTED period end, so it necessarily trails today — if it did not, "
        "this measure has been rebased onto the wall clock and the distinction is lost")


def test_the_allowance_clears_an_annual_series() -> None:
    """550d must not flag a merely-annual tag: up to ~365d behind a quarterly frontier, plus
    filing lag and a 53-week year. The nearest REAL abandonment measured is 670d."""
    assert 400 < STALE_TAG_LAG_DAYS < 670, (
        "the allowance must sit above a legitimate annual cadence and below the nearest measured "
        "abandonment (SMPL debt_current, 670d)")
