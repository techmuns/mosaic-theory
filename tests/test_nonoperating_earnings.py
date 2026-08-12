"""A quarter whose earnings are mostly non-operating cannot anchor a P/E, and nothing said so.

THE GAP. NFLX's Q1-2026 carries a **$2.59bn** Warner Bros. Discovery termination fee booked below
the operating line — 40% of pre-tax income — and UBER's Q2-2026 carries ~$1.39bn of investment
revaluation. Neither reaches any committed page. The CIQ unusual-items block is ANNUAL-only
(`financial_summary_annual`; the quarterly builder never calls `unusual_items_block`), so a
quarterly one-off has no route to the surface until it lands in a fiscal year, and before this
change NO XBRL non-operating concept was read at all — verified across two search vocabularies.

DERIVED, NOT PICKED, AND THE CORPUS IS WHY. The obvious build is "read a one-off gain tag". It does
not survive contact with the filings. UBER's Q2-2026 revaluation is carried by THREE overlapping
tags at THREE different values — `EquitySecuritiesFvNiUnrealizedGainLoss` 1,727M,
`DebtAndEquitySecuritiesGainLoss` 1,612M, `OtherNonoperatingIncomeExpense` 1,342M — and the
aggregate `NonoperatingIncomeExpense` is absent for roughly half the fleet and was abandoned by
UBER after 2025-09-30. Choosing among them is same-window/different-basis, the class the buyback
average was refused for. `pretax − operating` is the same block by the arithmetic of the income
statement, from two totals the filer states.

WHY BOTH THRESHOLD ARMS. Share-of-pre-tax says the item matters to an EPS read but its denominator
crosses zero — on the live corpus that alone yields MVST at 1,833% and AORT at 1,607% on items of
$14M and $5M. Share-of-revenue is the stabiliser. Measured on 13 names x 4 quarters, 20%/5% leaves
NFLX flagging on 2026-03-31 ALONE (quiet at 3-4% in its other three quarters).

AN OUTLIER TEST WAS TRIED FIRST AND THE MEASUREMENT REJECTED IT. Scoring each quarter against the
company's own trailing median catches NFLX (19x) and MISSES UBER (2.6x) — UBER revalues every
quarter, so a large non-operating swing IS its norm and its median rises to meet it. The reader's
question is not "is this unusual for them" but "how much of this is operating", which holds however
habitual the behaviour. Flagging novelty would have exempted the name that does it every quarter.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from vinci.dossier.mechanical import (
    _NONOP_PRETAX_SHARE,
    _NONOP_REVENUE_SHARE,
    _nonoperating_earnings,
    _quarterly_map,
)

FIX = Path("tests/fixtures/companyfacts")
REF = date(2026, 7, 29)


class _Stub:
    def __init__(self, facts: dict[str, Any]) -> None:
        self.facts = facts

    def companyfacts(self, cik: str) -> dict[str, Any]:
        return self.facts


def _run(ticker: str) -> Any:
    return _nonoperating_earnings(_Stub(json.loads((FIX / f"{ticker}.json").read_text())), "x", REF)


def _facts(**quarters: tuple[float, float, float]) -> dict[str, Any]:
    """A companyfacts dict in the REAL EDGAR shape: facts → ns → tag → units → rows.
    Each entry is ``period_end -> (operating, pretax, revenue)``."""
    def rows(idx: int) -> list[dict[str, Any]]:
        out = []
        for end, vals in quarters.items():
            e = date.fromisoformat(end.replace("_", "-"))
            out.append({"start": str(e.replace(month=((e.month - 3) or 12))), "end": str(e),
                        "val": vals[idx], "filed": str(e), "fy": e.year, "fp": "Q2",
                        "form": "10-Q", "accn": "x"})
        return out
    return {"facts": {"us-gaap": {
        "OperatingIncomeLoss": {"units": {"USD": rows(0)}},
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItems"
        "NoncontrollingInterest": {"units": {"USD": rows(1)}},
        "Revenues": {"units": {"USD": rows(2)}},
    }}}


# ─── the two cases that motivated it ──────────────────────────────────────────────────────────

@pytest.mark.skipif(not (FIX / "NFLX.json").is_file(), reason="no fixture")
def test_the_wbd_termination_fee_is_surfaced() -> None:
    """THE CASE THAT STARTED THIS. $2.59bn below the operating line in Q1-2026 — and it is NOT the
    latest quarter, which is exactly why the window is the trailing four: a latest-quarter-only
    read returns Q2's ordinary -$124M and says nothing, while the LTM EPS under a P/E still carries
    the whole fee."""
    out = _run("NFLX")
    assert out.value is not None, out.note
    assert "2,590" in out.value and "2026-03-31" in out.value, out.value
    assert "BELOW the operating line" in out.value
    assert "40% of pre-tax income" in out.value and "21% of revenue" in out.value
    assert "earlier quarter still inside the trailing four" in out.value, (
        "the reader is not told the item sits behind the latest quarter")


@pytest.mark.skipif(not (FIX / "UBER.json").is_file(), reason="no fixture")
def test_ubers_investment_revaluation_is_surfaced() -> None:
    """The name an outlier test would have missed: UBER revalues every quarter, so novelty is the
    wrong criterion and magnitude-vs-earnings is the right one."""
    out = _run("UBER")
    assert out.value is not None and "BELOW the operating line" in out.value, out.value
    assert "of revenue" in out.value


@pytest.mark.skipif(not (FIX / "UBER.json").is_file(), reason="no fixture")
def test_every_material_quarter_is_named_not_only_the_largest() -> None:
    """THE REGRESSION (2026-08-12, from an analyst reading UBER's page).

    UBER carries THREE material quarters and the page named ONE — the largest by revenue share,
    2025-09-30 — describing it as "an earlier quarter still inside the trailing four". A reader is
    then told the distortion sits behind them and the recent quarters are clean. Both dropped
    quarters are the RECENT ones, and 2026-06-30's +$1,387M is the investment revaluation the
    analyst raised AGAINST THIS VERY FIELD ("Q2 GAAP net income included a $1.6bn pre-tax benefit").

    The figure a reader divides by is an LTM one, so every quarter inside it counts."""
    out = _run("UBER")
    assert out.value is not None
    for quarter, amount in (("2025-09-30", "+$1,507M"),
                            ("2026-03-31", "−$1,427M"),
                            ("2026-06-30", "+$1,387M")):
        assert quarter in out.value, f"{quarter} is material and unnamed"
        assert amount in out.value, f"{quarter}'s magnitude is missing"
    assert out.value.startswith("3 of the trailing four quarters"), (
        "the count leads, so a reader knows how many items the LTM carries before reading them")


@pytest.mark.skipif(not (FIX / "UBER.json").is_file(), reason="no fixture")
def test_the_net_is_stated_because_the_largest_alone_overstates_it() -> None:
    """THE POINT THE MAXIMUM CANNOT MAKE. UBER's two unnamed quarters point OPPOSITE ways
    (−$1,427M then +$1,387M) and very nearly cancel, so naming only the +$1,507M implied a
    distortion the trailing figure does not carry. An LTM EPS carries the SUM."""
    out = _run("UBER")
    assert out.value is not None
    assert "netting +$1,521M across the four" in out.value, out.value
    assert "carries the SUM, not the largest" in out.value


def test_a_single_material_quarter_keeps_the_original_sentence() -> None:
    """THE BOUNDARY. One material quarter must read exactly as before — including the where-clause
    that tells a reader whether it is the latest quarter or sits behind it, which the multi-quarter
    list has no room for. NFLX (one material quarter) is pinned verbatim above; this holds the
    shape on a constructed one so the branch is covered without depending on a fixture."""
    # values in DOLLARS (the function renders $M): gap $400M = 80% of pre-tax, 40% of revenue
    facts = _facts(**{"2026_06_30": (100e6, 500e6, 1000e6)})
    out = _nonoperating_earnings(_Stub(facts), "x", REF)
    assert out.value is not None
    assert out.value.startswith("$400M of the quarter ended 2026-06-30 came from BELOW")
    assert "80% of pre-tax income, and 40% of revenue" in out.value
    assert "This is the latest quarter" in out.value
    assert "netting" not in out.value, "the single-quarter form must not grow a net clause"


@pytest.mark.skipif(not (FIX / "V.json").is_file(), reason="no fixture")
def test_an_ordinary_name_says_so_rather_than_going_silent() -> None:
    """NOT-MATERIAL IS A FINDING, not an absence — the field states what it checked and what it
    found, so a reader can tell "we looked, it's clean" from "nobody looked"."""
    out = _run("V")
    assert out.value is not None
    assert "no material non-operating item" in out.value
    assert "BELOW the operating line" not in out.value


# ─── the guards ───────────────────────────────────────────────────────────────────────────────

def test_the_three_legs_must_come_from_one_quarter() -> None:
    """SAME-WINDOW, ENFORCED BEFORE THE ARITHMETIC. Operating from one quarter minus pre-tax from
    another is not a non-operating figure — it is the buyback-average defect in a new place."""
    facts = _facts(**{"2026_06_30": (100.0, 500.0, 1000.0)})
    # …and move revenue to a DIFFERENT, still-well-formed quarter, so all three legs exist and
    # none of them share a period. (Editing only `end` would stretch the duration past the
    # quarterly filter and trip the missing-leg branch instead — a different guard entirely.)
    facts["facts"]["us-gaap"]["Revenues"]["units"]["USD"] = [
        {"start": "2026-01-01", "end": "2026-03-31", "val": 1000.0, "filed": "2026-05-01",
         "fy": 2026, "fp": "Q1", "form": "10-Q", "accn": "x"}]
    out = _nonoperating_earnings(_Stub(facts), "x", REF)
    assert out.value is None, out.value
    assert "never share a quarter" in (out.note or ""), out.note


def test_a_stale_preferred_alias_does_not_decide_the_period() -> None:
    """MEASURED DEFECT, and it is what the first cut shipped. `extract_points` is first-alias-WITH-
    DATA-wins, and an abandoned tag still has data — just old data. UBER stopped filing
    `RevenueFromContractWithCustomerExcludingAssessedTax` after 2019-06-30 and has used `Revenues`
    since, so the preferred alias handed back a SEVEN-YEAR-STALE quarter and the whole field
    resolved to 2019. `_quarterly_map` unions period coverage across aliases while keeping alias
    precedence WITHIN a period."""
    facts = _facts(**{"2026_06_30": (100.0, 500.0, 1000.0)})
    us = facts["facts"]["us-gaap"]
    # the preferred alias exists but is ancient; the fallback carries the current quarter
    us["RevenueFromContractWithCustomerExcludingAssessedTax"] = {"units": {"USD": [
        {"start": "2019-04-01", "end": "2019-06-30", "val": 7.0, "filed": "2019-08-01",
         "fy": 2019, "fp": "Q2", "form": "10-Q", "accn": "old"}]}}
    covered = _quarterly_map(facts, "revenue")
    assert date(2026, 6, 30) in covered, "the current quarter was lost to a stale preferred alias"
    assert covered[date(2019, 6, 30)] == 7.0, "alias precedence within a period was not preserved"
    out = _nonoperating_earnings(_Stub(facts), "x", REF)
    assert out.value is not None and "2026-06-30" in out.value, out.value


def test_both_arms_are_required() -> None:
    """Each arm alone admits a case the other rejects, so the AND is the design.

    Large share, tiny absolute (a thin quarter): must stay quiet — this is MVST's 1,833% shape.
    Large absolute, small share (a fat quarter): must stay quiet — nobody's EPS read is distorted.
    """
    thin = _facts(**{"2026_06_30": (100.0, 101.0, 5000.0)})   # gap 1 = 1% of pre-tax, 0.02% of rev
    assert "BELOW" not in (_nonoperating_earnings(_Stub(thin), "x", REF).value or "")
    # share arm passes (gap is 50% of pre-tax) but revenue arm fails (0.5% of revenue)
    share_only = _facts(**{"2026_06_30": (5.0, 10.0, 1000.0)})
    assert "BELOW" not in (_nonoperating_earnings(_Stub(share_only), "x", REF).value or "")
    # both arms pass
    both = _facts(**{"2026_06_30": (100.0, 400.0, 1000.0)})   # gap 300 = 75% pre-tax, 30% revenue
    assert "BELOW" in (_nonoperating_earnings(_Stub(both), "x", REF).value or "")


def test_a_near_zero_pre_tax_quarter_does_not_print_a_four_figure_percentage() -> None:
    """A quarter netting to ~zero pre-tax yields a share in the hundreds or thousands, which reads
    as a data error and buries the figure that is real. The revenue arm still carries the size."""
    facts = _facts(**{"2026_06_30": (100.0, 1.0, 500.0)})     # gap -99 = 9900% of pre-tax
    out = _nonoperating_earnings(_Stub(facts), "x", REF)
    assert out.value is not None and "BELOW the operating line" in out.value
    assert "9900%" not in out.value and "%" in out.value
    assert "nets near zero" in out.value, out.value
    assert "20% of revenue" in out.value, "the stable arm's figure was dropped too"


def test_an_exactly_zero_pre_tax_quarter_is_the_loudest_case_not_a_clean_one() -> None:
    """REVIEW FINDING (P1, #415). `pre == 0` made the share None, which dropped the quarter from
    `material` and printed "no material non-operating item" — the reassuring answer for the one
    shape that is maximally relevant: a below-the-line block that EXACTLY offsets operating income
    means the entire pre-tax result is non-operating.

    Not in today's corpus (the nearest are AORT at $339k and MVST at -$750k pre-tax, both already
    handled by the near-zero wording), so it is pinned on a fixture — a guard that has never fired
    is unproven until it is shown able to."""
    zero = _facts(**{"2026_06_30": (500.0, 0.0, 1000.0)})
    out = _nonoperating_earnings(_Stub(zero), "x", REF)
    assert out.value is not None and "BELOW the operating line" in out.value, out.value
    assert "nets near zero" in out.value, "the undefined share printed as a number"
    assert "50% of revenue" in out.value, "the arm that IS defined was dropped"
    # …and a zero gap on zero pre-tax is a true nothing, not a division artefact
    nothing = _facts(**{"2026_06_30": (0.0, 0.0, 1000.0)})
    assert "BELOW" not in (_nonoperating_earnings(_Stub(nothing), "x", REF).value or "")


def test_the_thresholds_are_the_measured_ones() -> None:
    """The constants are face-validity values derived from a stated measurement; pinning them makes
    a later edit state its own reason rather than drifting the calibration silently."""
    assert _NONOP_PRETAX_SHARE == 0.20
    assert _NONOP_REVENUE_SHARE == 0.05


def test_a_filer_without_the_pretax_tag_is_unknown_and_names_what_was_missing() -> None:
    """FAIL LOUD, NEVER GUESS — NCNO reports no quarterly pre-tax income at all, and the note has
    to say which leg was absent or a reader cannot tell a gap from a clean result."""
    out = _run("NCNO")
    assert out.value is None
    assert "pre-tax income" in (out.note or ""), out.note


# ─── the fleet ────────────────────────────────────────────────────────────────────────────────

@pytest.mark.skipif(not FIX.is_dir(), reason="no fixtures")
def test_the_flag_fires_on_a_minority_of_the_fleet() -> None:
    """SCOPE, pinned as a band rather than a name list. A check that fired on everything would be
    noise and one that fired on nothing would be dead; both are silent failures a green suite hides.
    Measured today: 4 of 15 flag, 9 clean, 2 UNKNOWN for a missing tag."""
    flagged = clean = unknown = 0
    for p in sorted(FIX.glob("*.json")):
        out = _nonoperating_earnings(_Stub(json.loads(p.read_text())), "x", REF)
        if out.value is None:
            unknown += 1
        elif "BELOW the operating line" in out.value:
            flagged += 1
        else:
            clean += 1
    total = flagged + clean + unknown
    assert flagged >= 1, "the check fires on nothing — it is dead"
    assert flagged <= total // 2, f"{flagged}/{total} flagged — the threshold has stopped selecting"
    assert clean >= 1, "nothing reads clean — the check has stopped discriminating"


@pytest.mark.skipif(not Path("data/dossiers").is_dir(), reason="no committed dossiers")
def test_every_committed_dossier_actually_carries_the_field() -> None:
    """REVIEW FINDING (P1, #415), and the sharper half of it: a field that only future assemblies
    populate ships NOTHING. The deployed pages and the JSON an LLM reads would still have carried
    `null`, so the $2.59bn WBD fee this change exists to surface would have stayed invisible on the
    very artifact the PR claimed to fix.

    PHRASING-INDEPENDENT BY CONSTRUCTION (TEST-LAYER RULE): asserts the field is POPULATED and that
    the flag reaches at least one page — never a specific figure, because these artifacts are
    re-assembled and re-struck. The value-level pins live on the frozen companyfacts fixtures above.

    FUBO is exempt BY DERIVATION, not by name: `known_wrong.json` seals it, and `refresh_dossier`
    refuses a transform on a sealed record — a page that says "do not trust these figures" must not
    acquire a freshly-computed one."""
    import json as _json

    missing, flagged = [], []
    for p in sorted(Path("data/dossiers").glob("*/dossier.json")):
        if (p.parent / "known_wrong.json").exists():
            continue
        q = (_json.loads(p.read_text()).get("mechanical") or {}).get("quality") or {}
        field = q.get("nonoperating_earnings")
        if field is None:
            missing.append(p.parent.name)
            continue
        if "BELOW the operating line" in (field.get("value") or ""):
            flagged.append(p.parent.name)
    assert not missing, (
        f"committed dossiers still carry a null non-operating field: {missing} — re-run the "
        f"artifact pass, or the page ships without the evidence this change adds")
    assert flagged, "the flag reaches no committed page — it would be shipping a field nobody sees"
