"""A restatement of a round figure is named (TeamNostra fix request 2, RE1-D6).

`concepts._same_figure` decides whether a later filing RESTATED a figure or only re-reported it at
another precision. companyfacts carries no `decimals`, so precision was guessed from each value's
trailing zeros — and a value that happens to be round looked coarse: 900,000,000 read as stated to
the $100 million, so NFLX's 885,849,000 "re-reported" it; HLF's diluted EPS of 3.30 (a float, 3.3)
read as stated to the dime, so its re-audit's 3.32 was "the same figure". On the 30 non-test
companyfacts fixtures, 70 of 1,769 later filings more than 0.5% from the first went unnamed so.

The rule now: a value's precision is still read from its trailing zeros (a filing can state
"$4.9 billion" — the precision-only re-reports below must stay unnamed), but never coarser than its
SECOND SIGNIFICANT FIGURE, and a per-share figure's never coarser than a CENT.

Every case below is a real row of a committed fixture (`tests/fixtures/companyfacts`), except the
four pairs TeamNostra's notes reproduce, which are pinned as they wrote them.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from vinci.edgar.concepts import (
    EVERY,
    ConceptPoint,
    _same_figure,
    filed_at,
    points_for_tag,
    superseded,
)

_FX = Path(__file__).resolve().parent / "fixtures" / "companyfacts"


def _facts(ticker: str) -> dict[str, Any]:
    return json.loads((_FX / f"{ticker}.json").read_text())  # type: ignore[no-any-return]


def _point(facts: dict[str, Any], tag: str, end: str, filed: str,
           start: str | None = None) -> ConceptPoint:
    """The one point of ``tag`` for the period ending ``end`` (from ``start``, for a duration)
    filed on ``filed``."""
    hits = [p for p in points_for_tag(facts, tag, currency=EVERY)
            if p.period_end == date.fromisoformat(end) and p.filed == date.fromisoformat(filed)
            and (p.period_start == (date.fromisoformat(start) if start else None))]
    assert len(hits) == 1, hits
    return hits[0]


# ─── ⊖ real restatements of a round figure, unnamed until now ──────────────────────────────────

@pytest.mark.parametrize(("ticker", "tag", "start", "end", "filed", "first", "first_filed"), [
    # HLF's re-audit (its 10-K/A of 2013-12-16): FY2011 diluted EPS 3.30 → 3.32
    ("HLF", "EarningsPerShareDiluted", "2011-01-01", "2011-12-31", "2013-12-16", 3.3,
     "2012-02-21"),
    # …and Q4 2012's 1.05 → 1.00
    ("HLF", "EarningsPerShareDiluted", "2012-10-01", "2012-12-31", "2013-12-16", 1.05,
     "2013-02-19"),
    # Verra Mobility's 10-K/A of 2021-05-17: Q3 2019 diluted EPS 0.11 → 0.10
    ("VRRM", "EarningsPerShareDiluted", "2019-07-01", "2019-09-30", "2021-05-17", 0.11,
     "2019-11-05"),
    # NFLX's FY2015 10-K nets issuance costs into its debt (ASU 2015-03): $900,000 thousand at
    # 2014-12-31 is restated to $885,849 thousand
    ("NFLX", "LongTermDebtNoncurrent", None, "2014-12-31", "2016-01-28", 900_000_000.0,
     "2015-01-29"),
    # MCK's recast of its Dec-2014 quarter: operating income $780 million → $800 million
    ("MCK", "OperatingIncomeLoss", "2014-10-01", "2014-12-31", "2016-01-27", 780_000_000.0,
     "2015-02-05"),
])
def test_a_restated_round_figure_is_named(ticker: str, tag: str, start: str | None, end: str,
                                          filed: str, first: float, first_filed: str) -> None:
    facts = _facts(ticker)
    p = _point(facts, tag, end, filed, start)
    old = superseded(facts, p)
    assert old is not None, f"{ticker} {tag} {p.value:,} restates {first:,} and is not named"
    assert (old.value, old.filed) == (first, date.fromisoformat(first_filed))
    # …and the citation a page prints says so
    assert f"first filed {first_filed}" in filed_at(p, facts)


# ─── ⊕ a precision-only re-report stays unnamed ────────────────────────────────────────────────

@pytest.mark.parametrize(("ticker", "tag", "start", "end", "filed"), [
    # AMZN's FY2015 depreciation, first filed as "$4.9 billion" (2017-02-10), later as 4,949 million
    ("AMZN", "Depreciation", "2015-01-01", "2015-12-31", "2018-02-02"),
    # Visa's AFS debt securities at FY2019's end: 6,267 million in the 10-K, "$6.3 billion" after
    ("V", "AvailableForSaleSecuritiesDebtSecurities", None, "2019-09-30", "2020-01-31"),
    # HLF's Q1 2010 net sales: 618,633 thousand in its 10-Q, 618.6 million in the 10-K's table
    ("HLF", "SalesRevenueNet", "2010-01-01", "2010-03-31", "2012-02-21"),
])
def test_a_re_report_at_another_precision_is_not_a_restatement(
        ticker: str, tag: str, start: str | None, end: str, filed: str) -> None:
    facts = _facts(ticker)
    p = _point(facts, tag, end, filed, start)
    assert superseded(facts, p) is None, f"{ticker} {tag} {p.value:,}"
    assert "restating" not in filed_at(p, facts)


# ─── the pairs TeamNostra's notes reproduce, as written there ─────────────────────────────────

@pytest.mark.parametrize(("a", "b", "unit"), [
    (200_000_000.0, 180_000_000.0, "USD"),
    (3_000_000_000.0, 2_600_000_000.0, "USD"),
    (0.4, 0.38, "USD/shares"),
    (-0.1, -0.12, "USD/shares"),
])
def test_the_notes_pairs_are_told_apart(a: float, b: float, unit: str) -> None:
    assert not _same_figure(a, b, unit=unit)


@pytest.mark.parametrize(("a", "b", "unit"), [
    (-69_100_000.0, -69_075_000.0, "USD"),   # #875's review: rounded to $100,000, not restated
    (4_900_000_000.0, 4_949_000_000.0, "USD"),
    (3.3, 3.3, "USD/shares"),
    (0.0, 0.0, "USD"),
])
def test_a_rounding_or_an_equal_figure_is_the_same_figure(a: float, b: float, unit: str) -> None:
    assert _same_figure(a, b, unit=unit)


def test_a_zero_carries_no_precision_of_its_own() -> None:
    """⊖ 0.0 has every trailing zero there is: read as stated to the dollar, it absorbed 0.40 per
    share (and, read at its own step, any figure under half of one)."""
    assert not _same_figure(0.0, 0.4, unit="USD/shares")
    assert not _same_figure(0.0, 400_000.0, unit="USD")


# ─── the corpus, read whole ────────────────────────────────────────────────────────────────────

def test_every_per_share_change_of_a_cent_is_named_across_the_corpus() -> None:
    """⊖ a per-share figure is stated to the cent, so on every committed fixture each later filing
    whose per-share figure moved by a cent or more is a restatement — 18 such pairs were read as
    "the same figure" (HLF's re-audit among them)."""
    missed, seen = [], 0
    for path in sorted(_FX.glob("*.json")):
        facts = json.loads(path.read_text())
        for tags in (facts.get("facts") or {}).values():
            for tag, node in tags.items():
                for unit, rows in (node.get("units") or {}).items():
                    if "/" not in unit:
                        continue
                    by_period: dict[tuple[Any, Any], list[dict[str, Any]]] = {}
                    for r in rows:
                        if r.get("val") is not None and r.get("filed"):
                            by_period.setdefault((r.get("start"), r["end"]), []).append(r)
                    for rs in by_period.values():
                        first = min(rs, key=lambda r: r["filed"])
                        for r in rs:
                            if r["filed"] > first["filed"] and \
                                    abs(r["val"] - first["val"]) >= 0.01 - 1e-9:
                                seen += 1
                                if _same_figure(first["val"], r["val"], unit=unit):
                                    missed.append(f"{path.stem} {tag} {r['end']}")
    assert seen > 0, "no per-share change in the corpus — the pin reads nothing"
    assert missed == [], f"{len(missed)} of {seen} per-share changes unnamed: {missed[:5]}"
